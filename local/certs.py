from time import time

from OpenSSL import crypto
from sqlalchemy import Column, Integer, String

from local.sql import Base
from local.settings import Settings


def generate_cert(request, domain):
    print('generate for', domain)
    settings = Settings.get_or_create(request.db)
    print('seettings')
    
    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, settings.ca_cert.encode('ascii'))
    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, settings.ca_key.encode('ascii'))
    key = crypto.load_privatekey(crypto.FILETYPE_PEM, settings.certs_key.encode('ascii'))

    print('ca_cert %s' % ca_cert)
    print('ca_key %s' % ca_key)

    cert = crypto.X509()
    cert.set_version(2)
    serial = int(time() * 1000)
    cert.set_serial_number(serial)

    subj = cert.get_subject()
    subj.commonName = domain.encode('ascii')

    cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', False, b'CA:FALSE'),
        crypto.X509Extension(b'subjectKeyIdentifier', False, b'hash', subject=cert),
    ])
    
    cert.add_extensions([
        crypto.X509Extension(b'authorityKeyIdentifier', False, b'keyid:always', issuer=ca_cert),
        crypto.X509Extension(b'keyUsage', False, b'digitalSignature, keyEncipherment'),
    ])

    alt_name = 'DNS:%s' % domain
    cert.add_extensions([
        crypto.X509Extension(b'subjectAltName', False, alt_name.encode('ascii')),
    ])

    print('_cert ok')

    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)

    ca_subj = ca_cert.get_subject()
    print('ca subj:: %s' % ca_subj)
    cert.set_issuer(ca_subj)
    
    print('privte ok')
    cert.set_pubkey(key)
    print('set_pubkey ok')
    cert.sign(ca_key, 'sha256')
    print('sign ok')

    with open('%s/%s.crt' % (request.certdir, domain), 'wb') as f:
        buf = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
        f.write(buf)

    print('saved')
