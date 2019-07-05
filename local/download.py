import enum

from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from local.sql import Base, Url


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
