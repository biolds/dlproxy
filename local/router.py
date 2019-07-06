import enum
import json
import mimetypes
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler

import urllib.parse
from sqlalchemy.inspection import inspect

from local.cacert import cacert
from local.download import Download


UI_PATH = 'dlui/dist/dlui/'
UI_INDEX = 'index.html'


def serialize(request, cls, obj_id, level):
    obj_id = int(obj_id)
    obj = request.db.query(cls).filter(cls.id == obj_id).one()

    r = {}
    for col in cls.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, enum.Enum):
            val = val.name
        r[col.name] = val

    # Nest serialize relationship
    if level > 0:
        level -= 1
        for key, val in inspect(cls).relationships.items():
            rel_id_attr = list(val.local_columns)[0].name
            rel_id = getattr(obj, rel_id_attr)
            r[key] = serialize(request, val.argument, rel_id, level)

    return r


def api_detail_view(cls, level, request, obj_id):
    r = serialize(request, cls, obj_id, level)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')


class Router:
    ROUTES = {
        'cacert': cacert,
        'api': {
            'download': lambda req, obj: api_detail_view(Download, 1, req, obj)
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
