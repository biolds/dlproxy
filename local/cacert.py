from local.settings import settings_get


def cacert_download(request):
    with open(request.cacert, 'rb') as f:
        data = f.read()
        request.send_content_response(data, 'application/x-x509-ca-cert')

def cacert_generate(request):
    settings_get(request)
