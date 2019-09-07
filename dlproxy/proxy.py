# -*- coding: utf-8 -*-
import argparse
import brotli
import sys
import os
import socket
import ssl
import select
import http.client
import urllib.parse
import threading
import zlib
import time
import json
import re
import cgi
from datetime import datetime
from traceback import format_exception
from ipaddress import ip_address
from html import unescape
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
from socketserver import ThreadingMixIn
from io import StringIO, BytesIO
from subprocess import Popen, PIPE
from string import Template

from sqlalchemy.orm.exc import NoResultFound, StaleDataError
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session

from dlproxy.access import UrlAccess
from dlproxy.certs import generate_cert
from dlproxy.download import Download
from dlproxy.index import load_index_content, render_index
from dlproxy.router import router
from dlproxy.sql import Base, Url, get_db_session, db_close_session
from dlproxy.searchs import Search, SearchResult
from dlproxy.search_engine import SearchEngine


def my_address(path=None):
    from dlproxy.conf import conf
    addr = conf.url
    if path:
        addr += path
    return addr


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    address_family = socket.AF_INET6
    daemon_threads = True

    def handle_error(self, request, client_address):
        # surpress socket/ssl related errors
        cls, e = sys.exc_info()[:2]
        if cls is socket.error or cls is ssl.SSLError:
            pass
        else:
            return HTTPServer.handle_error(self, request, client_address)


class ProxyRequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    cakey = 'ca.key'
    cacert = 'ca.crt'
    certkey = 'cert.key'
    certdir = 'certs/'
    timeout = 5
    lock = threading.Lock()

    def __init__(self, *args, **kwargs):
        self.tls = threading.local()
        self.tls.conns = {}

        BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

    def setup(self):
        super().setup()
        from dlproxy.conf import conf
        self.conf = conf
        self.db = get_db_session()
        print('new setup')

    def finished(self):
        db_close_session()

    def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.

        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                # An error code has been sent, just exit
                return

            # Normalize request path
            if self.path[0] == '/':
                if isinstance(self.connection, ssl.SSLSocket):
                    self.path = "https://%s%s" % (self.headers['Host'], self.path)
                else:
                    self.path = "http://%s%s" % (self.headers['Host'], self.path)

            my_addr = my_address().rstrip('/')
            my_addr = my_addr[len('http://'):]

            print('path %s / %s' % (self.path, my_addr))
            print('websocket %s' % self.headers.get('Upgrade'))
            # Relay CONNECT's to the web ui when dev is enabled
            if (self.path.startswith(my_address()) or self.path == my_addr) and (self.command != 'CONNECT' or not self.conf.dev):
                router.handle(self, self.conf)
            else:
                self.proxy_request()
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            self.log_error("Request timed out: %r", e)
            #a read or a write timed out.  Discard this connection
            self.close_connection = True
        except Exception as e:
            self.log_message("Exception on %s", self.path)
            self.log_error("Exception: %r", e)
            self.render_index(HTTPStatus.INTERNAL_SERVER_ERROR, 'error', exception=e)
            self.close_connection = True

    def proxy_request(self, inject=False):
        mname = 'do_' + self.command
        if not hasattr(self, mname):
            self.send_error(
                HTTPStatus.NOT_IMPLEMENTED,
                "Unsupported method (%r)" % self.command)
            return

        args = []
        if self.command == 'GET' and inject:
            args = [True]

        method = getattr(self, mname)

        res = None
        try:
            res = method(*args)
            self.wfile.flush()
        finally:
            if self.command != 'CONNECT' and not inject:
                mime = None
                status = 404
                is_ajax = bool(self.headers.get('X-Requested-With')) or self.path.endswith('.woff2')
                title = None

                if res:
                    mime = res.getheader('content-type', 'application/octet-stream')
                    if ';' in mime:
                        mime = mime.split(';', 1)[0]
                    status = res.status

                    if hasattr(res, 'title'):
                        title = res.title

                UrlAccess.log(self.db, self.path, title, mime, self.headers.get('Referer'), is_ajax, status)

                log_search = mime == 'text/html' and self.command in ('GET', 'POST')
                log_search = log_search and not is_ajax

                if log_search and status in (200, 302):
                    # Create search entry
                    search_match = SearchEngine.get_from_url(self.db, self.path)

                    if search_match is not None:
                        se, terms = search_match
                        search = Search.get_or_create(self.db, terms, se)
                        self.db.add(search)
                        self.db.commit()

                        if status == 302 and res and res.getheader('location') and search_match[0].store_results:
                            url = Url.get_or_create(self.db, res.getheader('location'))
                            search_res = SearchResult.get_or_create(self.db, search=search, url=url)
                            self.db.add(search_res)
                            self.db.commit()


                    if status == 200:
                    # Create search result entry where referers match a search query
                        search_match = SearchEngine.get_from_url(self.db, self.headers.get('referer'))

                        if search_match is not None and search_match[0].store_results:
                            se, terms = search_match
                            referer = Url.get_or_create(self.db, self.headers.get('Referer'))
                            url = Url.get_or_create(self.db, self.path)
                            search = Search.get_or_create(self.db, terms, se)
                            self.db.add(search)
                            search_res = SearchResult.get_or_create(self.db, search=search, url=url)
                            self.db.add(search_res)
                            self.db.commit()

                ping_from = self.headers.get('ping-from')
                ping_to = self.headers.get('ping-to')
                if status == 200 and self.command == 'POST' and ping_from and ping_to:
                    print('GOT pings %s %s' % (ping_from, ping_to))
                    search_match = SearchEngine.get_from_url(self.db, ping_from)

                    if search_match is not None:
                        se, terms = search_match
                        search = Search.get_or_create(self.db, terms, se)
                        self.db.add(search)
                        self.db.commit()

                        url = Url.get_or_create(self.db, ping_to)
                        search_res = SearchResult.get_or_create(self.db, search=search, url=url)
                        self.db.add(search_res)
                        self.db.commit()

    def render_index(self, status, *args, **kwargs):
        response = "%s %d %s\r\n" % (self.protocol_version, status.value, status.name)
        response = response.encode('ascii')
        self.wfile.write(response)

        if self.conf.dev and 'index' not in kwargs:
            # For error handling with the dev server index.html on angular dev server
            # is requested
            origin = ('http://', '127.0.0.1:4200')
            if not origin in self.tls.conns:
                self.tls.conns[origin] = http.client.HTTPConnection('127.0.0.1:4200', timeout=self.timeout)
            conn = self.tls.conns[origin]
            conn.request('GET', '/', None, {'Accept': 'text/html'})
            res = conn.getresponse()
            kwargs['index'] = res.read()

        content = render_index(self, self.conf, *args, **kwargs)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', len(content))
        self.send_header('Connection', 'close')
        self.end_headers()

        while len(content):
            buf = content[:1024]
            content = content[1024:]
            self.wfile.write(buf)

    def log_error(self, format, *args):
        # surpress "Request timed out: timeout('timed out',)"
        if isinstance(args[0], socket.timeout):
            return

        self.log_message(format, *args)

        ex = args[0]
        if isinstance(ex, Exception):
            exc = ''.join(format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
            self.log_message(exc.replace('%', '%%'))

    def do_CONNECT(self):
        address = self.path.split(':', 1)
        address[1] = int(address[1]) or 443

        my_addr = my_address().rstrip('/')
        my_addr = my_addr[len('http://'):]

        # Relay websocket in dev mode
        relay = (self.conf.dev is True and (self.path.startswith(my_address()) or self.path == my_addr))

        # Relay websocket on http
        relay |= address[1] == 80
        print('relaying: %s' % relay)

        #if os.path.isfile(self.cakey) and os.path.isfile(self.cacert) and os.path.isfile(self.certkey) and os.path.isdir(self.certdir):
        if relay:
            self.connect_relay()
        else:
            self.connect_intercept()

    def connect_intercept(self):
        hostname = self.path.split(':')[0]
        certpath = "%s/%s.crt" % (self.certdir.rstrip('/'), hostname)
        confpath = "%s/%s.cnf" % (self.certdir.rstrip('/'), hostname)

        print('intercept')
        with self.lock:
            if not os.path.isfile(certpath):
                generate_cert(self, hostname)

        resp = "%s %d %s\r\n" % (self.protocol_version, 200, 'Connection Established')
        resp = resp.encode('ascii')
        self.wfile.write(resp + b'\r\n')
        #self.end_headers()

        print('new conn: %s / %s' % (self.certkey, certpath))
        self.connection = ssl.wrap_socket(self.connection, keyfile=self.certkey, certfile=certpath, server_side=True)
        self.rfile = self.connection.makefile("rb", self.rbufsize)
        self.wfile = self.connection.makefile("wb", self.wbufsize)

        conntype = self.headers.get('Proxy-Connection', '')
        if conntype.lower() == 'close':
            self.close_connection = 1
        elif (conntype.lower() == 'keep-alive' and self.protocol_version >= "HTTP/1.1"):
            self.close_connection = 0

    def connect_relay(self):
        address = self.path.split(':', 1)
        address[1] = int(address[1]) or 443
        timeout = self.timeout

        my_addr = my_address().rstrip('/')
        my_addr = my_addr[len('http://'):]
        relay_self = (self.conf.dev is True and (self.path.startswith(my_address()) or self.path == my_addr))

        if relay_self:
            is_websocket = True
            address = ('127.0.0.1', 4200)

        try:
            s = socket.create_connection(address, timeout=self.timeout)
        except Exception as e:
            raise
            self.send_error(502)
            return

        #self.send_response(200, 'Connection Established')
        #self.end_headers()
        resp = "%s %d %s\r\n" % (self.protocol_version, 200, 'Connection Established')
        resp = resp.encode('ascii')
        self.wfile.write(resp + b'\r\n')

        self._relay(s)

    def _relay(self, s, is_websocket=False):
        conns = [self.connection, s]
        self.close_connection = 0
        print('CONNECTed')

        check_websocket = True
        while not self.close_connection:
            timeout = self.timeout
            if is_websocket:
                # Firefox network.http.keep-alive.timeout
                timeout = 115
            rlist, wlist, xlist = select.select(conns, [], conns, timeout)
            if xlist or not rlist:
                print('xlist %s rlist %s' % (xlist, rlist))
                break

            for r in rlist:
                other = conns[1] if r is conns[0] else conns[0]
                data = r.recv(8192)
                if not data:
                    print('relay no data')
                    self.close_connection = 1
                    break
                print('%s -> %s : %s' % (r, other, data))

                if check_websocket:
                    check_websocket = False
                    if data[:4] == b'GET ':
                        print('found websocket')
                        is_websocket = True
                    else:
                        print('found non websocket')

                other.sendall(data)
        print('CONNECT to %s closed' % self.path)

    def do_GET(self, inject=False):
        download = False
        res = None
        req = self
        content_length = int(req.headers.get('Content-Length', 0))
        req_body = self.rfile.read(content_length) if content_length else None

        u = urllib.parse.urlsplit(req.path)
        scheme, netloc, path = u.scheme, u.netloc, (u.path + '?' + u.query if u.query else u.path)
        assert scheme in ('http', 'https')
        if netloc:
            req.headers['Host'] = netloc

        if req.headers.get('Upgrade') != 'websocket':
            req_headers = self.filter_headers(req.headers.items())
        else:
            req_headers = req.headers
            for header in req_headers.keys():
                if header.lower() in ('proxy-authenticate', 'proxy-authorization'):
                    req_headers.pop(header)

        try:
            origin = (scheme, netloc)
            if not origin in self.tls.conns:
                if scheme == 'https':
                    self.tls.conns[origin] = http.client.HTTPSConnection(netloc, timeout=self.timeout)
                else:
                    self.tls.conns[origin] = http.client.HTTPConnection(netloc, timeout=self.timeout)
                print('new origi %s' % netloc)
            conn = self.tls.conns[origin]
            conn.request(self.command, path, req_body, dict(req_headers))
            res = conn.getresponse()
            version_table = {10: 'HTTP/1.0', 11: 'HTTP/1.1'}
            setattr(res, 'headers', res.msg)
            setattr(res, 'response_version', version_table[res.version])
            is_download, filename = self._is_download(netloc, path, res)
            print('download:', is_download)
            print('status %s' % res.status)
            if inject:
                print('inject/content-type:', res.getheader('content-type'))

            if is_download and self.command in ('GET', 'POST') and res.status >= 200 and res.status < 300:
                if '/' in filename:
                    _, filename = filename.rsplit('/', 1)
                filename = filename.replace('\\', '').lstrip('.')
                db_url = Url.get_or_create(self.db, req.path)
                download = Download(url=db_url, filesize=res.getheader('content-length', 0), filename=filename, mimetype=res.getheader('content-type'))
                self.db.add(download)
                self.db.commit()
                self.send_response(302)
                fd = open(download.get_path_cache(), 'wb')
                download_id = download.id
                self.send_header('Location', my_address('download/%s' % download.id))
                self.end_headers()
            elif inject and self.conf.dev is True and (res.getheader('content-type') == 'text/html'
                                                or res.getheader('content-type',  '').startswith('text/html;')):
                print('injecting live')
                self.render_index(HTTPStatus.OK, 'angular', index=res.read())
                return res
            else:
                response = "%s %d %s\r\n" % (self.protocol_version, res.status, res.reason)
                self.wfile.write(response.encode('ascii'))

                if res.headers.get('Upgrade') != 'websocket':
                    res_headers = self.filter_headers(res.getheaders())
                else:
                    res_headers = res.headers
                    for header in res_headers.keys():
                        if header.lower() in ('proxy-authenticate', 'proxy-authorization'):
                            res_headers.pop(header)
                    res_headers = res_headers.items()

                for key, val in res_headers:
                    header = '%s: %s\r\n' % (key, val)
                    self.wfile.write(header.encode('ascii'))
                self.wfile.write(b'\r\n')
                fd = self.wfile

            if self.headers.get('Upgrade') == 'websocket':
                if res.status != 101:
                    print('error: %s' % res.read())
                print('got wwebsocket')
                return self._relay(conn.sock, True)

            i = 0
            has_title = ((res.getheader('content-type') == 'text/html' or res.getheader('content-type',  '').startswith('text/html;'))
                and not self.headers.get('X-Requested-With') and res.status >= 200 and res.status < 300)

            if has_title:
                content = b''
                content_lower = b''
                print('has_title %s %s' % (has_title, res.getheader('content-encoding', '')))

                gzip_obj = None
                if res.getheader('content-encoding') == 'gzip':
                    gzip_obj = zlib.decompressobj(zlib.MAX_WBITS + 16)
                elif res.getheader('content-encoding') == 'br':
                    gzip_obj = brotli.Decompressor()

            while True:
                res_body = res.read(1024)
                if len(res_body) == 0:
                    break
                fd.write(res_body)

                if has_title and len(content) < 50 * 1024:
                    if gzip_obj:
                        data = gzip_obj.decompress(res_body)
                    else:
                        data = res_body

                    if content == b'':
                        print(b'content:\n%s' % data)

                    content += data
                    content_lower += data.lower()

                    start = content_lower.find(b'<html>')
                    if start == -1:
                        start = content_lower.find(b'<html ')
                    if start == -1:
                        start = content_lower.find(b'<html\n')
                    print('HTML tag: %s' % start)


                    if start != -1:
                        print('HTML found')
                        for tag in (b'head', b'title'):
                            tag_start = content_lower.find(b'<%s>' % tag, start)
                            if tag_start == -1:
                                break
                            print('%s found' % tag.upper().decode('ascii'))
                            start = tag_start
                        else:
                            end = content_lower.find(b'</title>', start)

                            if end != -1:
                                title = content[start + len(b'<title>'):end].decode('utf-8')
                                res.title = unescape(title)
                                print('found title: %s' % res.title)
                                has_title = False

                if i % 16 == 0 and download:
                    try:
                        self.db.flush()
                        download = self.db.query(Download).get(download.id)

                        # Check the entry in the db still exists, to cancel the download otherwise
                        if download is None:
                            break

                        now = datetime.now()
                        dt = now - download.stats_date
                        download.bandwidth = (16 * 1024) / dt.total_seconds()
                        download.stats_date = now
                        self.db.add(download)
                        self.db.commit()
                    except StaleDataError:
                        # Download was canceled and sql update failed
                        download = None
                        self.db.rollback()
                        break

                i += 1

            fd.flush()

            if download:
                download = self.db.query(Download).get(download.id)
                filesize = download.filesize
                download.update_from_file(self.db)

                if filesize != download.filesize and download.filesize != 0:
                    download.error = 'Connection closed'

                self.db.add(download)
                self.db.commit()

            self.log_request(res.status, res.reason)
        except Exception as e:
            if origin in self.tls.conns:
                del self.tls.conns[origin]
            if download:
                download = self.db.query(Download).get(download.id)
                download.update_from_file(self.db)
                exc = ''.join(format_exception(etype=type(e), value=e, tb=e.__traceback__))
                download.error = exc
                print('downlad got exception:\n%s' % exc)
                self.db.add(download)
                self.db.commit()

            self.send_error(502, repr(e))
            raise
        return res

    def _is_download(self, netloc, path, res):
        if self.headers.get('X-Requested-With'):
            return False, None

        if ':' in netloc:
            netloc = netloc.split(':', 1)[0]

        try:
            ip_addr = ip_address(netloc)
        except ValueError:
            ip_addr = socket.gethostbyname(netloc)
            ip_addr = ip_address(ip_addr)

        if ip_addr.is_private:
            return False, None


        print('is_download path: %s' % path)
        if path == '/manifest.json':
            return False, None

        if netloc == 'www.google.com' and path.startswith('/async/'):
            return False, None

        if netloc in ('googleads.g.doubleclick.net', 'sb-ssl.google.com', 'safebrowsing.googleapis.com',
                        'clientservices.googleapis.com'):
            return False, None

        for domain in ('.gvt1.com',):
            if netloc.endswith(domain):
                return False, None

        for ext in ('wasm', 'pb', 'ttf', 'woff', 'woff2'):
            if path.endswith('.' + ext):
                return False,  None

        content_type = res.getheader('Content-Type', '')
        if ';' in content_type:
            content_type = content_type.split(';', 1)[0]

        for mime in ('application/x-font', 'application/font', 'application/vnd.', 'application/opensearchdescription'):
            if content_type.startswith(mime):
                return False, None
        if content_type in ('text/javascript', 'application/javascript', 'application/x-javascript',
                'application/x-www-form-urlencoded', 'application/json', 'application/x-protobuf', 'application/x-protobuffer',
                'application/json+protobuf', 'application/x-chrome-extension'):
            return False, None

        # Google calendar / chat ...
        if netloc.endswith('google.com') and content_type == 'application/gzip':
            return False, None

        print('headers:', res.getheaders())
        disposition = res.getheader('Content-Disposition', '')
        #if disposition.startswith('inline;'):
        #    return False, None

        #if disposition == 'attachment':
        #    return False, None

        if disposition.startswith('attachment;'):
            disps = [disp.strip() for disp in disposition.split(';')][1:]
            for disp in disps:
                # TODO: select utf8 filename if present
                if disp.startswith('filename='):
                    print('disp:', disposition)
                    disp = disp[len('filename='):]
                    disp = disp.strip('"')
                    return True, disp


        print('type:', content_type)
        if not content_type.startswith('application/'):
            return False, None

        u = urllib.parse.urlsplit(self.path)
        url = urllib.parse.unquote_plus(u.path)
        return True, os.path.basename(url)

    do_HEAD = do_GET
    do_POST = do_GET
    do_OPTIONS = do_GET

    def filter_headers(self, headers):
        # http://tools.ietf.org/html/rfc2616#section-13.5.1
        hop_by_hop = ('connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'transfer-encoding', 'upgrade')
        _headers = []
        for key, val in headers:
            if key.lower() not in hop_by_hop:
                _headers.append((key, val))
        return _headers

    def send_content_response(self, content, content_type, allow_origin=False):
        response = "%s %d %s\r\n" % (self.protocol_version, 200, 'OK')
        response = response.encode('ascii')
        self.wfile.write(response)

        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(content))
        self.send_header('Connection', 'close')
        if allow_origin:
            self.send_header('Access-Control-Allow-Origin', 'http://piggledy.org')
            self.send_header('Vary', 'Origin')
        self.end_headers()

        while len(content):
            buf = content[:1024]
            content = content[1024:]
            self.wfile.write(buf)

