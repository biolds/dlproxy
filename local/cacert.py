def cacert(request):
    with open(request.cacert, 'rb') as f:
        data = f.read()
        request.send_content_response(data, 'application/x-x509-ca-cert')
