from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import NoResultFound


Base = declarative_base()


class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    ca_cert = Column(String(1024))
    ca_key = Column(String(1024))


class Url(Base):
    __tablename__ = 'url'
    id = Column(Integer, primary_key=True)
    url = Column(String(65536))

    @classmethod
    def get_or_create(cls, db, url):
        res = db.query(Url).filter_by(url=url).first()
        if res:
            return res

        try:
            with db.begin_nested():
                instance = Url(url=url)
                db.add(instance)
                return instance
        except IntegrityError:
            return db.query(Url).filter_by(url=url).one()


def init_db(conf, engine):
    import local.access
    import local.download
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
