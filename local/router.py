import urllib.parse

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
            request.send_response(404)
            request.end_headers()
        else:
            view(request)

router = Router()
