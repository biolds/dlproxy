from sqlalchemy import BigInteger, DateTime, Column, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from local.sql import Base, Url


class Download(Base):
    __tablename__ = 'download'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship(Url)
    date = Column(DateTime, default=func.now())
    filesize = Column(BigInteger)
