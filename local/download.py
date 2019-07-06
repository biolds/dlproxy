import enum
import json
import os

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from local.sql import Base, Url
from local.view import serialize


class DownloadState(enum.Enum):
    undecided = 0
    in_progress = 1
    finished = 2


class Download(Base):
    __tablename__ = 'download'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship(Url)
    date = Column(DateTime, default=func.now())
    filesize = Column(BigInteger)
    state = Column(Enum(DownloadState), default=DownloadState.undecided)

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
