import tempfile
import subprocess

from local.settings import Settings, settings_get


def cacert_download(request):
    settings = Settings.get_or_create(request.db)
    data = settings.ca_cert.encode('ascii')

    response = "%s %d %s\r\n" % (request.protocol_version, 200, 'OK')
    response = response.encode('ascii')
    request.wfile.write(response)
    request.send_header('Content-Type', 'application/x-x509-ca-cert')
    request.send_header('Content-Length', len(data))
    request.send_header('Content-Disposition', 'attachment; filename="cacert.crt"')
    request.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    request.send_header('Pragma', 'no-cache')
    request.send_header('Expires', '0')
    request.send_header('Connection', 'close')
    request.end_headers()
    request.wfile.write(data)


def cacert_generate(request):
    if request.command != 'POST':
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    with tempfile.TemporaryDirectory() as tmpdirname:
        from proxy2 import my_hostname
        print('created temporary directory', tmpdirname)
        subprocess.run('''
            cd "%s"
            umask 0077
            openssl genrsa -out ca.key 4096
            openssl req -new -x509 -days 3650 -key ca.key -out ca.crt -subj "/CN=%s CA"
            openssl genrsa -out cert.key 4096
        ''' % (tmpdirname, my_hostname), shell=True, check=True)

        settings = Settings.get_or_create(request.db)
        with open('%s/ca.crt' % tmpdirname, 'rb') as f:
            settings.ca_cert = f.read().decode('ascii')
        with open('%s/ca.key' % tmpdirname, 'rb') as f:
            settings.ca_key = f.read().decode('ascii')
        request.db.add(settings)
        request.db.commit()

    settings_get(request)
