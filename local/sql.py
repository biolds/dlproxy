from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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


def init_db(conf, engine):
    import local.access
    import local.download
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
