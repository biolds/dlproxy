import json

from sqlalchemy import DateTime, Column, ForeignKey, Integer, String, func, or_
from sqlalchemy.orm import relationship

from dlproxy.sql import Base, Url
from dlproxy.view import list_serialize, ilike_escape


class UrlAccess(Base):
    __tablename__ = 'url_access'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship(Url, foreign_keys=[url_id])
    referer_id = Column(Integer, ForeignKey('url.id'))
    referer = relationship(Url, foreign_keys=[referer_id])
    status = Column(Integer)

    @classmethod
    def log(cls, db, url, title, mime, referer, is_ajax, status):
        url = Url.get_or_create(db, url, title, mime, is_ajax)
        referer_url = None
        if referer:
            referer_url = Url.get_or_create(db, referer)
        access = UrlAccess(url=url, referer=referer_url, status=status)
        db.add(access)
        db.commit()


def url_accesses(request, query):
    filters = []
    if 'q' in query:
        q = query.get('q')[0]

        for term in q.split():
            print('adding term %s' % term)
            term = ilike_escape(term)
            filters.append((UrlAccess.url.has(Url.url.ilike(term))) | 
                           (UrlAccess.url.has(Url.title.ilike(term))))

    with_dates = False
    if 'with_dates' in query and query.get('with_dates')[0] == '1':
        with_dates = True

    r = list_serialize(request, query, UrlAccess, 1, 30, filters, with_dates=with_dates)
    r = json.dumps(r).encode('ascii')
    request.send_content_response(r, 'application/json')
