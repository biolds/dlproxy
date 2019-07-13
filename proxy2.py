# -*- coding: utf-8 -*-
import argparse
import sys
import os
import socket
import ssl
import select
import http.client
import urllib.parse
import threading
import gzip
import zlib
import time
import json
import re
import cgi
from ipaddress import ip_address
from http.server import HTTPServer, BaseHTTPRequestHandler, HTTPStatus
from socketserver import ThreadingMixIn
from io import StringIO, BytesIO
from subprocess import Popen, PIPE

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

from local.access import UrlAccess
from local.download import Download
from local.index import load_index_content, render_index
from local.router import router
from local.sql import Base, Url

download_html = '''
<html>
<head>
  <title>{filename}</title>
  <script src="http://code.jquery.com/jquery-3.1.0.min.js"
          integrity="sha256-cCueBR6CsyA4/9szpPfrX3s49M9vUU5BgtiJj06wt/s="
          crossorigin="anonymous"></script>
</head>
<body>
<h1>{filename}</h1>
<form action="https://proxy2.post" method="POST" enctype="x-www-form-urlencoded">
    <input type="hidden" name="path" value="{path}" />
    <input type="hidden" name="filename" value="{filename}" />
    <input type="hidden" name="size" value="{size}" />
    <input type="hidden" name="mimetype" value="{mimetype}" />
    <input type="hidden" name="origin" value="{origin}" />
    <input type="radio" name="action" value="store" checked>Store</input>
    <input type="radio" name="action" value="download">Download</input>
    <input type="submit" value="Submit">
</form>
</body>
</html>
'''

my_hostname = socket.gethostname()
conf = None

engine = create_engine('postgresql+psycopg2://dlproxy:dlproxy@localhost:5432/dlproxy') #, echo=True)
session_factory = sessionmaker(bind=engine)
DBSession = scoped_session(session_factory)


def my_address(path=None):
    global conf
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
    protocol = 'HTTP/1.1'

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
        global DBSession
        self.db = DBSession()
        print('new setup')

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

            db_url = UrlAccess.log(self.db, self.path, self.headers['Referer'])

            print('path %s' % self.path)
            if self.path.startswith(my_address()):
                global conf
                router.handle(self, conf)
            else:
                self.proxy_request()
            self.wfile.flush() #actually send the response if not already done.
        except socket.timeout as e:
            self.log_error("Request timed out: %r", e)
            #a read or a write timed out.  Discard this connection
            self.close_connection = True
        except Exception as e:
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
        if self.command == 'GET':
            args = [True]

        method = getattr(self, mname)
        method(*args)

    def render_index(self, status, *args, **kwargs):
        response = "%s %d %s\r\n" % (self.protocol_version, status.value, status.name)
        response = response.encode('ascii')
        self.wfile.write(response)

        global conf
        if conf.dev and 'index' not in kwargs:
            # For error handling with the dev server index.html on angular dev server
            # is requested
            origin = ('http://', '127.0.0.1:4200')
            if not origin in self.tls.conns:
                self.tls.conns[origin] = http.client.HTTPConnection('127.0.0.1:4200', timeout=self.timeout)
            conn = self.tls.conns[origin]
            conn.request('GET', '/', None, {'Accept': 'text/html'})
            res = conn.getresponse()
            kwargs['index'] = res.read()

        content = render_index(conf, *args, **kwargs)
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

        from traceback import format_exception
        ex = args[0]
        if isinstance(ex, Exception):
            exc = ''.join(format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
            print('exc')
            self.log_message(exc)

    def do_CONNECT(self):
        if os.path.isfile(self.cakey) and os.path.isfile(self.cacert) and os.path.isfile(self.certkey) and os.path.isdir(self.certdir):
            self.connect_intercept()
        else:
            self.connect_relay()

    def connect_intercept(self):
        hostname = self.path.split(':')[0]
        certpath = "%s/%s.crt" % (self.certdir.rstrip('/'), hostname)

        with self.lock:
            if not os.path.isfile(certpath):
                epoch = "%d" % (time.time() * 1000)
                p1 = Popen(["openssl", "req", "-new", "-key", self.certkey, "-subj", "/CN=%s" % hostname], stdout=PIPE)
                p2 = Popen(["openssl", "x509", "-req", "-days", "3650", "-CA", self.cacert, "-CAkey", self.cakey, "-set_serial", epoch, "-out", certpath], stdin=p1.stdout, stderr=PIPE)
                p2.communicate()

        resp = "%s %d %s\r\n" % (self.protocol_version, 200, 'Connection Established')
        resp = resp.encode('ascii')
        self.wfile.write(resp + b'\r\n')

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
        try:
            s = socket.create_connection(address, timeout=self.timeout)
        except Exception as e:
            self.send_error(502)
            return
        self.send_response(200, 'Connection Established')
        self.end_headers()

        conns = [self.connection, s]
        self.close_connection = 0
        while not self.close_connection:
            rlist, wlist, xlist = select.select(conns, [], conns, self.timeout)
            if xlist or not rlist:
                break
            for r in rlist:
                other = conns[1] if r is conns[0] else conns[0]
                data = r.recv(8192)
                if not data:
                    self.close_connection = 1
                    break
                other.sendall(data)

    def do_GET(self, inject=False):
        req = self
        content_length = int(req.headers.get('Content-Length', 0))
        req_body = self.rfile.read(content_length) if content_length else None

        if req.path == 'https://proxy2.post/':
            self.download_post(req_body)
            return

        u = urllib.parse.urlsplit(req.path)
        scheme, netloc, path = u.scheme, u.netloc, (u.path + '?' + u.query if u.query else u.path)
        assert scheme in ('http', 'https')
        if netloc:
            req.headers['Host'] = netloc
        req_headers = self.filter_headers(req.headers.items())

        try:
            origin = (scheme, netloc)
            if not origin in self.tls.conns:
                if scheme == 'https':
                    self.tls.conns[origin] = http.client.HTTPSConnection(netloc, timeout=self.timeout)
                else:
                    self.tls.conns[origin] = http.client.HTTPConnection(netloc, timeout=self.timeout)
            conn = self.tls.conns[origin]
            conn.request(self.command, path, req_body, dict(req_headers))
            res = conn.getresponse()
            version_table = {10: 'HTTP/1.0', 11: 'HTTP/1.1'}
            setattr(res, 'headers', res.msg)
            setattr(res, 'response_version', version_table[res.version])
            download, filename = self._is_download(netloc, res)
            print('download:', download)
            if inject:
                print('inject/content-type:', res.getheader('content-type'))

            if download:
                filename = filename.replace('/', '').replace('\\', '').lstrip('.')
                db_url = Url.get_or_create(self.db, req.path)
                download = Download(url=db_url, filesize=res.getheader('content-length', 0), filename=filename, mimetype=res.getheader('content-type'))
                fd = open(download.get_path_cache(), 'wb')
                self.db.add(download)
                self.db.commit()
                self.send_response(302)
                download_id = download.id
                self.send_header('Location', my_address('download/%s' % download.id))
                self.end_headers()
            elif inject and conf.dev is True and (res.getheader('content-type') == 'text/html'
                                                or res.getheader('content-type',  '').startswith('text/html;')):
                print('injecting live')
                self.render_index(HTTPStatus.OK, 'angular', index=res.read())
                return
            else:
                response = "%s %d %s\r\n" % (self.protocol_version, res.status, res.reason)
                self.wfile.write(response.encode('ascii'))
                res_headers = self.filter_headers(res.getheaders())
                for key, val in res_headers:
                    header = '%s: %s\r\n' % (key, val)
                    self.wfile.write(header.encode('ascii'))
                self.wfile.write(b'\r\n')
                fd = self.wfile

            while True:
                res_body = res.read(1024)
                if len(res_body) == 0:
                    break
                fd.write(res_body)

                # Check the entry in the db still exists, to cancel the download otherwise
                if download:
                    try:
                        self.db.flush()
                        self.db.query(Download).get(download.id)
                    except NoResultFound:
                        print('CANCELED')
                        break

            fd.flush()
            self.log_request(res.status, res.reason)
        except Exception as e:
            if origin in self.tls.conns:
                del self.tls.conns[origin]
            self.send_error(502, repr(e))
            raise

    def _is_download(self, netloc, res):
        if ':' in netloc:
            netloc = netloc.split(':', 1)[0]

        try:
            ip_addr = ip_address(netloc)
        except ValueError:
            ip_addr = socket.gethostbyname(netloc)
            ip_addr = ip_address(ip_addr)

        if ip_addr.is_private:
            return False, None

        print('headers:', res.getheaders())
        disposition = res.getheader('Content-Disposition', '')
        #if disposition.startswith('inline;'):
        #    return False, None

        if disposition.startswith('attachment;') or disposition.startswith('inline;'):
            disps = [disp.strip() for disp in disposition.split(';')][1:]
            for disp in disps:
                # TODO: select utf8 filename if present
                if disp.startswith('filename='):
                    print('disp:', disposition)
                    disp = disp[len('filename='):]
                    disp = disp.strip('"')
                    return True, disp

        content_type = res.getheader('Content-Type', '')
        if ';' in content_type:
            content_type = content_type.split(';', 1)[0]

        print('type:', content_type)
        if not content_type.startswith('application/'):
            return False, None
        for mime in ('application/x-font', 'application/font', 'application/vnd.'):
            if content_type.startswith(mime):
                return False, None

        if content_type in ('application/javascript', 'application/x-javascript',
                'application/x-www-form-urlencoded', 'application/json'):
            return False, None

        u = urllib.parse.urlsplit(self.path)
        return True, os.path.basename(u.path)

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

    def send_download_page(self, path, filename, size, mimetype):
        # Redirect
        origin = self.path
        if self.headers.get('referer', ''):
            origin = self.headers.get('referer')
        html = download_html.format(path=path, filename=filename, size=size, mimetype=mimetype, origin=origin)
        html = html.encode('ascii')
        self.send_content_response(html, 'text/html')

    def download_post(self, req_body):
        data = urllib.parse.parse_qsl(req_body.decode('ascii'))
        data = dict(data)
        print('data:', data)
        data['filename'] = data['filename'].replace('/', '_')
        data['path'] = data['path'].replace('/', '_')
        if data['action'] == 'store':
            os.rename('cache/' + data['path'], 'downloads/' + data['filename'])
            self.send_response(302)
            self.send_header('Location', data['origin'])
            self.end_headers()
            return
        elif data['action'] != 'download':
            raise Exception('bad action')

        f = open('cache/' + data['path'], 'rb')
        os.unlink('cache/' + data['path'])

        response = "%s %d %s\r\n" % (self.protocol_version, 200, 'OK')
        response = response.encode('ascii')
        self.wfile.write(response)
        self.send_header('Content-Type', data['mimetype'])
        self.send_header('Content-Length', data['size'])
        self.send_header('Content-Disposition', 'attachment; filename="%s"' % data['filename'])
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.send_header('Connection', 'close')
        self.end_headers()

        size = int(data['size'])
        while size:
            n = 1024 if size > 1024 else size
            buf = f.read(n)
            if buf == 0:
                sleep(1)
                continue

            self.wfile.write(buf)
            size -= len(buf)
        self.wfile.flush()
        f.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    default_url = 'http://%s:%i/' % (my_hostname, 8000)
    parser.add_argument('--init-db', action='store_true', help='Create database tables')
    parser.add_argument('--dev', action='store_true', help='Serve UI through Angular development server (on localhost:4200)')
    parser.add_argument('-p', '--port', type=int, help='Port number to listen on', default=8000)
    parser.add_argument('-u', '--url', type=int, help='Public url (default %s)' % default_url, default=None)
    conf = parser.parse_args()

    if conf.init_db:
        from local.sql import init_db
        init_db(conf, engine)
        print('Done')
        sys.exit(0)

    if conf.url is None:
        conf.url = 'http://%s:%i/' % (my_hostname, conf.port)

    if not conf.dev:
        load_index_content(conf)

    server_address = ('', conf.port)
    httpd = ThreadingHTTPServer(server_address, ProxyRequestHandler)

    sa = httpd.socket.getsockname()
    print('Serving', my_address(), 'HTTP Proxy on', sa[0], 'port', sa[1], '...')
    httpd.serve_forever()
