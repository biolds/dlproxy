import urllib.parse
from http.server import BaseHTTPRequestHandler

from local.cacert import cacert


class Router:
    ROUTES = {
        'cacert': cacert
    }

    def handle(self, request):
        u = urllib.parse.urlsplit(request.path)
        scheme, netloc, path = u.scheme, u.netloc, (u.path + '?' + u.query if u.query else u.path)

        view = self.ROUTES.get(path.split('/')[1])
        if view is None:
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
            view(request)

router = Router()
