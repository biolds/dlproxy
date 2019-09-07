import threading

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound


Base = declarative_base()


class Url(Base):
    __tablename__ = 'url'
    id = Column(Integer, primary_key=True)
    url = Column(String(65536))
    title = Column(String(1024))
    mimetype = Column(String(64))
    is_ajax = Column(Boolean())

    @classmethod
    def get_or_create(cls, db, url, title=None, mime=None, is_ajax=False):
        instance = db.query(Url).filter_by(url=url).first()
        if not instance:
            try:
                with db.begin_nested():
                    instance = Url(url=url, title=title, mimetype=mime, is_ajax=is_ajax)
                    db.add(instance)
                    return instance
            except IntegrityError:
                instance = db.query(Url).filter_by(url=url).one()

        for var, attr in ((title, 'title'), (mime, 'mimetype'), (is_ajax, 'is_ajax')):
            if var and var != getattr(instance, attr):
                setattr(instance, attr, var)
                db.add(instance)

        return instance


def _get_engine():
    engine = create_engine('postgresql+psycopg2://dlproxy:dlproxy@localhost:5432/dlproxy',
                max_overflow=-1 # allow unlimited connections since, threads count is not limited
                ) #, echo=True)
    return engine


DBSession = None


def get_db_session():
    import local.access
    import local.download
    import local.proxy
    import local.search_engine
    import local.searchs
    import local.settings

    global DBSession
    if DBSession is None:
        engine = _get_engine()
        session_factory = sessionmaker(bind=engine)
        DBSession = scoped_session(session_factory)
    return DBSession()


def db_close_session():
    DBSession.remove()


def db_reset():
    #import local.access
    #import local.download
    engine = _get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def db_startup_cleaning(db):
    from local.download import Download

    print('db_startup_cleaning %s' % db)
    print('got %s' % list(db.query(Download).filter(Download.to_keep == False)))
    for download in db.query(Download).filter(Download.to_keep == False):
        db.delete(download)
    for download in db.query(Download).filter(Download.downloaded == False):
        download.update_from_file(db)
        db.add(download)
    db.commit()
