from sqlalchemy import DateTime, Column, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from local.sql import Base, Url


class UrlAccess(Base):
    __tablename__ = 'url_access'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship(Url, foreign_keys=[url_id])
    referer_id = Column(Integer, ForeignKey('url.id'))
    referer = relationship(Url, foreign_keys=[referer_id])

    @classmethod
    def log(cls, db, url, referer):
        url = Url.get_or_create(db, url)
        referer = Url.get_or_create(db, referer)
        access = UrlAccess(url=url, referer=referer)
        db.add(access)
        db.commit()
