from datetime import datetime, timedelta
from urllib.parse import quote_plus
import json

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, desc, func
from sqlalchemy.orm import relationship

from local.search_engine import SearchEngine
from local.sql import Base, Url
from local.view import serialize


class Search(Base):
    __tablename__ = 'search'
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=func.now())
    query = Column(String(2048))
    search_engine_id = Column(Integer, ForeignKey('search_engine.id'))
    search_engine = relationship(SearchEngine)

    @classmethod
    def get_or_create(cls, db, query, search_engine):
        # Take last same query within last 10 mins
        instance = db.query(Search).filter(
            Search.query == query,
            Search.search_engine == search_engine,
            Search.date >= datetime.now() - timedelta(minutes=10),
        ).first()

        if not instance:
            # Take last query if its the same
            instance = db.query(Search).order_by(desc(Search.date)).first()
            if instance and (instance.query != query or instance.search_engine != search_engine):
                instance = None

        if not instance:
            instance = Search(query=query, search_engine=search_engine)
            db.add(instance)

        return instance


class SearchResult(Base):
    __tablename__ = 'search_result'
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('url.id'))
    url = relationship(Url)
    search_id = Column(Integer, ForeignKey('search.id'))
    search = relationship(Search)

    @classmethod
    def get_or_create(cls, db, search, url):
        instance = db.query(SearchResult).filter_by(search=search, url=url).first()

        if not instance:
            instance = SearchResult(search=search, url=url)
            db.add(instance)

        return instance


def last_searches(request, query):
    searches = request.db.query(Search).order_by(desc(Search.date)).limit(100)
    search_ids = [r.id for r in searches]
    results = request.db.query(SearchResult).filter(Search.id.in_(search_ids))

    resp = {
        'count': searches.count(),
        'offset': 0,
        'objs': []
    }

    for s in searches:
        search_obj = serialize(request, Search, s.id, 1)
        search_obj['results'] = []
        resp['objs'].append(search_obj)

    for r in results:
        resp_idx = search_ids.index(r.search_id)
        resp['objs'][resp_idx]['results'].append(serialize(request, Url, r.url_id, 0))

    resp = json.dumps(resp).encode('ascii')
    request.send_content_response(resp, 'application/json')
