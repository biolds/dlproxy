import argparse
import os
import socket
from configparser import ConfigParser


my_hostname = socket.gethostname()
conf = None


CONF_OPTIONS = {
    'port': str,
    'url': str,
    'dev': bool,
    'port': int
}

def conf_value(field, val):
    if CONF_OPTIONS[field] == bool:
        try:
            val = ('false', 'true').index(val.lower())
            return bool(val)
        except IndexError:
            raise Exception('Invalid value for boolean conf entry: %s' % field)
    elif CONF_OPTIONS[field] == int:
        return int(val)
    return val


def get_conf():
    global conf
    global my_hostname

    if not conf:
        parser = argparse.ArgumentParser()

        parser.add_argument('--init-db', action='store_true', help='Create database tables')
        parser.add_argument('--dev', action='store_true', help='Serve UI through Angular development server (on localhost:4200)')
        parser.add_argument('-c', '--config', type=str, action='store', help='Configuration file', default='/etc/dlproxy/dlproxy.conf')
        #parser.add_argument('-p', '--port', type=int, help='Port number to listen on', default=8000)
        #parser.add_argument('-u', '--url', help='Public url (default %s)' % default_url, default=None)

        conf = parser.parse_args()

        if not os.path.exists(conf.config):
            raise Exception('Config file %s does not exist' % conf.config)

        print('reading conf file')
        conf_parser = ConfigParser()
        conf_parser.read(conf.config)
        print('parsed conf:\n%s' % dict(conf_parser['main'].items()))

        if not conf_parser['main'].get('url'):
            default_url = 'http://%s:%i/' % (my_hostname, 8000)
            conf.url = default_url

        for key, val in conf_parser['main'].items():
            if key not in CONF_OPTIONS:
                raise Exception('Invalid configuration option: %s' % key)
            val = conf_value(key, val)
            if key in ('dev',):
                conf.dev |= val
            else:
                setattr(conf, key, val)

        print('Current configuration:\n%s' % conf.__dict__)
    return conf
