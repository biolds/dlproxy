from OpenSSL import crypto

from dlproxy.settings import Settings, settings_get


def cacert_download(request, query):
    settings = Settings.get_or_create(request.db)
    data = settings.ca_cert.encode('ascii')

    response = '%s %d %s\r\n' % (request.protocol_version, 200, 'OK')
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


def cacert_generate(request, query):
    if request.command != 'POST':
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    from proxy2 import my_hostname
    # Based on https://stackoverflow.com/questions/45873832/how-do-i-create-and-sign-certificates-with-pythons-pyopenssl

    # CA key and certificate
    ca_key = crypto.PKey()
    ca_key.generate_key(crypto.TYPE_RSA, 4096)

    ca_cert = crypto.X509()
    ca_cert.set_version(2)
    ca_cert.set_serial_number(1)

    ca_subj = ca_cert.get_subject()
    ca_subj.commonName = '%s CA' % my_hostname

    ca_cert.add_extensions([
        crypto.X509Extension(b'subjectKeyIdentifier', False, b'hash', subject=ca_cert),
    ])

    ca_cert.add_extensions([
        crypto.X509Extension(b'authorityKeyIdentifier', False, b'keyid:always', issuer=ca_cert),
    ])

    ca_cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', False, b'CA:TRUE'),
        crypto.X509Extension(b'keyUsage', False, b'keyCertSign, cRLSign'),
    ])

    ca_cert.set_issuer(ca_subj)
    ca_cert.set_pubkey(ca_key)
    ca_cert.sign(ca_key, 'sha256')

    ca_cert.gmtime_adj_notBefore(0)
    ca_cert.gmtime_adj_notAfter(10*365*24*60*60)

    settings = Settings.get_or_create(request.db)
    settings.ca_cert = crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert).decode('ascii')
    settings.ca_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key).decode('ascii')

    # Key to generate certificates
    certs_key = crypto.PKey()
    certs_key.generate_key(crypto.TYPE_RSA, 4096)
    settings.certs_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, certs_key).decode('ascii')

    request.db.add(settings)
    request.db.commit()

    settings_get(request)
