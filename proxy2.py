# -*- coding: utf-8 -*-
import argparse
import socket
import sys
import os

from local.access import UrlAccess
from local.certs import generate_cert
from local.download import Download
from local.index import load_index_content, render_index
from local.proxy import ThreadingHTTPServer, ProxyRequestHandler, my_address
from local.router import router
from local.sql import Base, Url, db_reset, db_startup_cleaning, get_db_session
from local.searchs import Search, SearchResult
from local.search_engine import SearchEngine


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    my_hostname = socket.gethostname()
    default_url = 'http://%s:%i/' % (my_hostname, 8000)
    parser.add_argument('--init-db', action='store_true', help='Create database tables')
    parser.add_argument('--dev', action='store_true', help='Serve UI through Angular development server (on localhost:4200)')
    parser.add_argument('-p', '--port', type=int, help='Port number to listen on', default=8000)
    parser.add_argument('-u', '--url', help='Public url (default %s)' % default_url, default=None)
    from local import proxy
    proxy.conf = parser.parse_args()
    conf = proxy.conf

    if conf.init_db:
        db_reset()
        print('Done')
        sys.exit(0)

    if conf.url is None:
        conf.url = 'http://%s:%i/' % (my_hostname, conf.port)

    if not conf.dev:
        load_index_content(conf)

    db = get_db_session()

    # Clean previously running downloads
    db_startup_cleaning(db)

    for f in os.listdir('cache/'):
        os.unlink('cache/' + f)

    # Parse search engines
    for f in os.listdir('search/'):
        if f.endswith('.xml'):
            SearchEngine.parse_xml_file(db, 'search/' + f)
        elif f.endswith('.yaml'):
            SearchEngine.parse_yaml_file(db, 'search/' + f)

    server_address = ('', conf.port)
    httpd = ThreadingHTTPServer(server_address, ProxyRequestHandler)

    sa = httpd.socket.getsockname()
    print('Serving', my_address(), 'HTTP Proxy on', sa[0], 'port', sa[1], '...')
    httpd.serve_forever()
