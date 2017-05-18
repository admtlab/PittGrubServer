import json
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


def init(engine, create=False):
    """Initialize database"""
    global session
    session = scoped_session(sessionmaker(bind=engine))
    if create:
        Base.metadata.create_all(bind=engine)


class Test(Base):
    __tablename__ = 'Test'
    executor = 1
    
    id = Column(Integer, primary_key=True)

    @classmethod
    def get_all(self):
        return session.query(Test).all()

    @classmethod
    def get_by_id(self, id: int):
        value = session.query(Test).get(id)
        return value

    def to_json(self):
        return(json.dumps({u'id': self.id}))

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Tornado(Base):
    __tablename__ = 'Tornado'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    def serialize(self):
        return json.dumps({'id': self.id, 'name': self.name})