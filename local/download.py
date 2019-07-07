from http.server import HTTPStatus
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
    mimetype = Column(String(64))
    to_keep = Column(Boolean, default=False)
    downloaded = Column(Boolean, default=False)


    def get_path_cache(self):
        return 'cache/' + self.url.url.replace('/', '_')


def download_view(request, obj_id):
    r = serialize(request, Download, obj_id, 1)
    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)

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
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)
    download.to_keep = True
    request.db.add(download)
    request.db.commit()

    os.rename(download.get_path_cache(), 'downloads/' + download.filename)
    request.send_content_response('{}'.encode('ascii'), 'application/json')


def download_delete(request, obj_id):
    if request.command != 'POST':
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)
    file_path = download.get_path_cache()
    request.db.delete(download)
    request.db.commit()
    os.unlink(file_path)

    request.send_content_response('{}'.encode('ascii'), 'application/json')

def direct_download(request, obj_id):
    if request.command != 'POST':
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)
    request.db.delete(download)
    request.db.commit()

    f = open(download.get_path_cache(), 'rb')
    os.unlink(download.get_path_cache())

    response = "%s %d %s\r\n" % (request.protocol_version, 200, 'OK')
    response = response.encode('ascii')
    request.wfile.write(response)
    request.send_header('Content-Type', download.mimetype)
    request.send_header('Content-Length', download.filesize)
    request.send_header('Content-Disposition', 'attachment; filename="%s"' % downoad.filename)
    request.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    request.send_header('Pragma', 'no-cache')
    request.send_header('Expires', '0')
    request.send_header('Connection', 'close')
    request.end_headers()

    size = int(download.filesize)
    while size:
        n = 1024 if size > 1024 else size
        buf = f.read(n)
        if buf == 0:
            sleep(1)
            continue

        request.wfile.write(buf)
        size -= len(buf)
    request.wfile.flush()
    f.close()
