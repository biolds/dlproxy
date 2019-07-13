import mimetypes
import os
from http.server import BaseHTTPRequestHandler

import urllib.parse

from local.cacert import cacert_download, cacert_generate
from local.download import download_delete, download_view, download_save, direct_download
from local.settings import settings_view
from local.index import render_index, UI_INDEX, UI_PATH


class Router:
    ROUTES = {
        'cacert_download': cacert_download,
        'direct_download': direct_download,
        'api': {
            # 'download': lambda req, obj: api_detail_view(Download, 1, req, obj)
            'download': {
                'get': download_view,
                'save': download_save,
                'delete': download_delete
            },
            'cacert': {
                'generate': cacert_generate,
            },
            'settings': settings_view
        }
    }

    def handle(self, request, conf):
        u = urllib.parse.urlsplit(request.path)
        scheme, netloc, path = u.scheme, u.netloc, (u.path + '?' + u.query if u.query else u.path)

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
                path = request.path.split('/')
                path[2] = '127.0.0.1:4200'
                request.path = '/'.join(path)
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
                    request.send_content_response(render_index(conf, 'angular'), 'text/html')
                else:
                    mime = mimetypes.guess_type(path)[0]
                    with open(path, 'rb') as p:
                        request.send_content_response(p.read(), mime, mime == 'application/javascript')
        else:
            print('params:', _path)
            view(request, *_path)

router = Router()
