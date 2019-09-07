import argparse
import socket


my_hostname = socket.gethostname()
conf = None


def get_conf():
    global conf
    global my_hostname

    if not conf:
        parser = argparse.ArgumentParser()

        default_url = 'http://%s:%i/' % (my_hostname, 8000)
        parser.add_argument('--init-db', action='store_true', help='Create database tables')
        parser.add_argument('--dev', action='store_true', help='Serve UI through Angular development server (on localhost:4200)')
        parser.add_argument('-c', '--config', type=str, action='store', help='Configuration file', default='/etc/dlproxy/dlproxy.conf')
        parser.add_argument('-p', '--port', type=int, help='Port number to listen on', default=8000)
        parser.add_argument('-u', '--url', help='Public url (default %s)' % default_url, default=None)

        conf = parser.parse_args()

    return conf
