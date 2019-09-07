import json

from traceback import format_exception


UI_PATH = 'dlui/dist/dlui/'
UI_INDEX = 'index.html'

index_content = ''


def index_base_inject(content, my_address):
    content = content.replace('src="', 'src="%s' % my_address)
    content = content.replace('<!-- EXTENSION SCRIPT HERE -->', '''<script type="text/javascript">
        %s
        // EXTENSION SCRIPT HERE
    </script>
    ''' % format_var('myAddress', my_address))
    return content


def load_index_content(conf):
    content = open('%s/%s' % (UI_PATH, UI_INDEX)).read()
    content = index_base_inject(content, conf.url)
    global index_content
    index_content = content


def format_var(name, value):
    return 'let %s = %s;\n' % (name, json.dumps(value))


def render_index(request, conf, page, index=None, exception=None):
    if not 'text/html' in request.headers.get('accept', 'text/html') and exception:
        if conf.dev:
            err = ''.join(format_exception(etype=type(exception), value=exception, tb=exception.__traceback__))
        else:
            err = repr(exception)
        return err.encode('ascii')

    globalvars = {
        'page': page,
        'error': {
            'message': '',
            'traceback': ''
        }
    }

    if exception:
        exc = {
            'message': str(exception),
            'traceback': ''
        }
        if conf.dev:
            exc['traceback'] = ''.join(format_exception(etype=type(exception), value=exception, tb=exception.__traceback__))
        globalvars['error'] = exc

    script = ''

    for key, val in globalvars.items():
        script += format_var(key, val)

    if conf.dev:
        index = index.decode('ascii')
        content = index_base_inject(index, conf.url)
    else:
        global index_content
        content = index_content
    return content.replace('// EXTENSION SCRIPT HERE', script).encode('ascii')
