import mimetypes
import os
from http.server import BaseHTTPRequestHandler

import urllib.parse

from dlproxy.access import UrlAccess, url_accesses
from dlproxy.cacert import cacert_download, cacert_generate
from dlproxy.download import dl_download, download_delete, downloads_view, download_view, download_save, direct_download
from dlproxy.index import render_index, UI_INDEX, UI_PATH
from dlproxy.searchs import SearchResult, last_searches
from dlproxy.search_engine import SearchEngine, search_redirect, search_ods
from dlproxy.settings import settings_view
from dlproxy.view import api_list_view


class Router:
    ROUTES = {
        'cacert_download': cacert_download,
        'direct_download': direct_download,
        'dl_download': dl_download,
        'dl_open': lambda req, q, obj_id: dl_download(req, q, obj_id, attachment=False),
        'search': search_redirect,
        'search_ods.xml': search_ods,
        'api': {
            'downloads': downloads_view,
            'download': {
                'get': download_view,
                'save': download_save,
                'delete': download_delete
            },
            'cacert': {
                'generate': cacert_generate,
            },
            'settings': settings_view,
            'urls': url_accesses,
            'search_engines': lambda req, q: api_list_view(SearchEngine, 0, req, q),
            'search_results': lambda req, q: api_list_view(SearchResult, 1, req, q),
            'last_searches': last_searches
        }
    }

    def handle(self, request, conf):
        u = urllib.parse.urlsplit(request.path)
        scheme, netloc, path = u.scheme, u.netloc, u.path
        request.conf = conf

        # TODO heck referer of unsfe methods

        view = self.ROUTES
        _path = path.split('/')[1:]

        print('start path:', path)
        while view is not None and len(_path) and isinstance(view, dict):
            print('current path:', path)
            view = view.get(_path.pop(0))
            print('viiew:', view)

        if view is None or isinstance(view, dict):
            if conf.dev:
                print('request.path: %s' % request.path)
                if '/' in request.path:
                    path = request.path.split('/')
                    path[2] = '127.0.0.1:4200'
                    request.path = '/'.join(path)
                else:
                    request.path = '127.0.0.1:4200'
                print('proxy with inject')
                request.proxy_request(inject=True)
            else:
                path = path.lstrip('/')
                if path == '':
                    path = UI_INDEX

                print('init path ', path)
                path = os.path.normpath(path)
                print('normed ', path)
                if path.startswith('/') or path.startswith('../'):
                    path = UI_INDEX

                path = UI_PATH + path
                print('want ', path)
                if not os.path.isfile(path):
                    path = UI_PATH + UI_INDEX

                if path == UI_PATH + UI_INDEX:
                    request.send_content_response(render_index(request, conf, 'angular'), 'text/html')
                else:
                    mime = mimetypes.guess_type(path)[0]
                    with open(path, 'rb') as p:
                        request.send_content_response(p.read(), mime, mime == 'application/javascript')
        else:
            if len(_path) and _path[-1] == '':
                # strip trailing /
                _path = _path[:-1]
            print('params:', _path)

            query = urllib.parse.parse_qs(u.query)
            view(request, query, *_path)

router = Router()
