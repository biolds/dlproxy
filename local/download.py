import json
import os

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from local.sql import Base, Url
from local.view import serialize


class Download(Base):
    __tablename__ = 'download'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship(Url)
    date = Column(DateTime, default=func.now())
    filesize = Column(BigInteger)
    filename = Column(String(4096))
    to_keep = Column(Boolean, default=False)
    downloaded = Column(Boolean, default=False)


    def get_path_cache(self):
        return 'cache/' + self.url.url.replace('/', '_')


def download_view(request, obj_id):
    r = serialize(request, Download, obj_id, 1)
    obj_id = int(obj_id)
    download = request.db.query(Download).filter(Download.id == obj_id).one()

    current_size = 0
    try:
        statinfo = os.stat(download.get_path_cache())
        current_size = statinfo.st_size
    except:
        raise

    r['current_size'] = current_size
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')


def download_save(request, obj_id):
    if request.command != 'POST':
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    obj_id = int(obj_id)
    download = request.db.query(Download).filter(Download.id == obj_id).one()
    download.to_keep = True
    request.db.add(download)
    request.db.commit()

    os.rename(download.get_path_cache(), 'downloads/' + download.filename)
    request.send_content_response('{}'.encode('ascii'), 'application/json')


def download_delete(request, obj_id):
    if request.command != 'POST':
        self.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    obj_id = int(obj_id)
    download = request.db.query(Download).filter(Download.id == obj_id).one()
    request.db.add(download)
    request.db.commit()

    os.rename(download.get_path_cache(), 'downloads/' + download.filename)
    request.send_content_response('{}'.encode('ascii'), 'application/json')
