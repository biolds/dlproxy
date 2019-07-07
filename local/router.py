import mimetypes
import os
from http.server import BaseHTTPRequestHandler

import urllib.parse

from local.cacert import cacert
from local.download import download_view, download_save


UI_PATH = 'dlui/dist/dlui/'
UI_INDEX = 'index.html'


class Router:
    ROUTES = {
        'cacert': cacert,
        'api': {
            # 'download': lambda req, obj: api_detail_view(Download, 1, req, obj)
            'download': {
                'get': download_view,
                'save': download_save
            }
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
            #from proxy2 import conf
            if conf.dev:
                path = request.path.split('/')
                path[2] = '127.0.0.1:4200'
                request.path = '/'.join(path)
                request.proxy_request()
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
                    path = UI_PATH + '/' + UI_INDEX

                mime = mimetypes.guess_type(path)[0]
                with open(path, 'rb') as p:
                    request.send_content_response(p.read(), mime)
        else:
            view(request, *_path)

router = Router()
