import enum
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler

import urllib.parse
from sqlalchemy.inspection import inspect

from local.cacert import cacert
from local.download import Download


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

    def handle(self, request):
        u = urllib.parse.urlsplit(request.path)
        scheme, netloc, path = u.scheme, u.netloc, (u.path + '?' + u.query if u.query else u.path)

        # TODO heck referer of unsfe methods

        view = self.ROUTES
        path = path.split('/')[1:]

        print('start path:', path)
        while view is not None and len(path) and isinstance(view, dict):
            print('current path:', path)
            view = view.get(path.pop(0))
            print('viiew:', view)

        if view is None or isinstance(view, dict):
            from proxy2 import DEV
            if DEV:
                path = request.path.split('/')
                path[2] = '127.0.0.1:4200'
                request.path = '/'.join(path)
                request.proxy_request()
            else:
                raise Exception('to do')
                #request.send_response(404)
                #request.end_headers()
        else:
            view(request, *path)

router = Router()
