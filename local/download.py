from http.server import HTTPStatus
import json
import os

import magic
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound

from local.sql import Base, Url
from local.view import list_serialize, serialize


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
    stats_date = Column(DateTime, default=func.now())
    bandwidth = Column(Integer, default=None)
    error = Column(String(4096))

    def get_path_cache(self):
        return 'cache/%i' % self.id

    def update_from_file(self, db):
        self.downloaded = True
        self.stats_date = None
        self.bandwidth = None

        if self.to_keep:
            filepath = 'downloads/%s' % self.filename
        else:
            filepath = self.get_path_cache()

        self.filesize = os.stat(filepath).st_size

        m = magic.Magic(mime=True, uncompress=False)
        mime = m.from_file(filepath)
        if ';' in mime:
            mime = mime.split(';', 1)[0]
        self.mimetype = mime


def downloads_view(request):
    downloads = list_serialize(request, Download, {}, 1)
    for d in downloads['objs']:
        if d['downloaded']:
            d['current_size'] = d['filesize']
        elif d['to_keep']:
            d['current_size'] = os.stat('downloads/%s' % d['filename']).st_size
        else:
            fpath = 'cache/%i' % d['id']
            d['current_size'] = os.stat(fpath).st_size

    downloads = json.dumps(downloads).encode('ascii')
    request.send_content_response(downloads, 'application/json')


def download_view(request, obj_id):
    obj_id = int(obj_id)

    try:
        r = serialize(request, Download, obj_id, 1)
    except NoResultFound:
        request.send_error(HTTPStatus.NOT_FOUND)
        return

    download = request.db.query(Download).get(obj_id)

    if download.to_keep:
        statinfo = os.stat('downloads/%s' % download.filename)
    else:
        statinfo = os.stat(download.get_path_cache())

    current_size = statinfo.st_size
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

    # Find a non-existent filename
    if '.' in download.filename:
        file_prefix, file_suffix = download.filename.rsplit('.', 1)
    else:
        file_prefix, file_suffix = download.filename, ''

    i = 0
    while True:
        filename = '%s (%i)' % (file_prefix, i) if i else file_prefix
        if file_suffix:
            filename += '.' + file_suffix

        if not os.path.exists('downloads/' + filename):
            break

        i += 1

    download.filename = filename

    os.rename(download.get_path_cache(), 'downloads/' + filename)
    request.db.add(download)
    request.db.commit()
    download_view(request, obj_id)


def download_delete(request, obj_id):
    if request.command != 'POST':
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)
    if download.to_keep:
        file_path = 'downloads/%s' % download.filename
    else:
        file_path = download.get_path_cache()
    request.db.delete(download)
    request.db.commit()
    os.unlink(file_path)

    request.send_content_response('{}'.encode('ascii'), 'application/json')


def direct_download(request, obj_id):
    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)

    if download.to_keep:
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    filename = download.filename
    filesize = download.filesize
    mime = download.mimetype
    filepath = download.get_path_cache()
    request.db.delete(download)
    request.db.commit()

    f = open(filepath, 'rb')
    os.unlink(filepath)

    response = "%s %d %s\r\n" % (request.protocol_version, 200, 'OK')
    response = response.encode('ascii')
    request.wfile.write(response)
    request.send_header('Content-Type', mime)
    request.send_header('Content-Length', filesize)
    request.send_header('Content-Disposition', 'attachment; filename="%s"' % filename)
    request.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    request.send_header('Pragma', 'no-cache')
    request.send_header('Expires', '0')
    request.send_header('Connection', 'close')
    request.end_headers()

    size = int(filesize)
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


def dl_download(request, obj_id, attachment=True):
    obj_id = int(obj_id)
    download = request.db.query(Download).get(obj_id)

    if not download.to_keep:
        request.send_error(HTTPStatus.METHOD_NOT_ALLOWED)
        return

    filename = download.filename
    filesize = download.filesize
    mime = download.mimetype
    filepath = 'downloads/' + filename

    f = open(filepath, 'rb')

    response = "%s %d %s\r\n" % (request.protocol_version, 200, 'OK')
    response = response.encode('ascii')
    request.wfile.write(response)
    request.send_header('Content-Type', mime)
    request.send_header('Content-Length', filesize)
    if attachment:
        content_disp = 'attachment'
    else:
        content_disp = 'inline'
    content_disp += '; filename="%s"' % filename
    request.send_header('Content-Disposition', content_disp)
    request.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
    request.send_header('Pragma', 'no-cache')
    request.send_header('Expires', '0')
    request.send_header('Connection', 'close')
    request.end_headers()

    size = int(filesize)
    i = 0
    while size:
        n = 1024 if size > 1024 else size
        buf = f.read(n)
        if len(buf) == 0:
            i += 1

            # Check the download still exists
            if i % 16 == 0:
                self.db.flush()
                download = self.db.query(Download).get(obj_id)
                if download is None:
                    break
                size = download.filesize

            sleep(1)
            continue
        else:
            i = 0

        request.wfile.write(buf)
        size -= len(buf)
    request.wfile.flush()
    f.close()
