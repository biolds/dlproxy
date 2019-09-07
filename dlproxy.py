# -*- coding: utf-8 -*-
import sys
import os

from dlproxy.access import UrlAccess
from dlproxy.certs import generate_cert
from dlproxy.conf import get_conf, my_hostname
from dlproxy.download import Download
from dlproxy.index import load_index_content, render_index
from dlproxy.proxy import ThreadingHTTPServer, ProxyRequestHandler, my_address
from dlproxy.router import router
from dlproxy.sql import Base, Url, db_reset, db_startup_cleaning, get_db_session
from dlproxy.searchs import Search, SearchResult
from dlproxy.search_engine import SearchEngine


if __name__ == '__main__':
    conf = get_conf()
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
