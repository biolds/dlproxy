import json

from sqlalchemy import Column, Integer, String

from local.sql import Base
from local.view import serialize


class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    ca_cert = Column(String(65536), default='abc')
    ca_key = Column(String(65536), default='def')

    @classmethod
    def get_or_create(cls, db):
        res = db.query(Settings).get(1)
        print('res fond:', res)
        if res:
            return res

        try:
            instance = Settings()
            db.add(instance)
            db.commit()
            return instance
        except IntegrityError:
            return db.query(Settings).get(1)


def settings_get(request):
    settings = Settings.get_or_create(request.db)
    print('got:', settings)
    r = serialize(request, Settings, settings.id, 0)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')


def settings_view(request):
    if request.command == 'POST':
        print('PSOT')
        content_length = int(request.headers.get('Content-Length', 0))
        data = request.rfile.read(content_length) if content_length else None
        data = json.loads(data.decode('ascii'))
        print('daa %s' % data)
        settings = Settings.get_or_create(request.db)
        for attr in ('ca_cert', 'ca_key'):
            if attr in data:
                print('settings %s' % attr)
                setattr(settings, attr, data[attr])
        request.db.add(settings)
        request.db.commit()

    settings_get(request)
