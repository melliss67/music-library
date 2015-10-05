from sqlalchemy import Column, ForeignKey, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)


class Releases(Base):
    __tablename__ = 'releases'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,ForeignKey('users.id'))
    title = Column(String(250), nullable=False)
    artist = Column(String(250), nullable=False)
    release_date = Column(String(30))
    label = Column(String(50))
    catalog_number = Column(String(30))
    barcode = Column(String(30))
    mbid = Column(Integer)
    asin = Column(Integer)
    format = Column(String(30))

    
class PageMe(Base):
    __tablename__ = 'page_me'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))


engine = create_engine('sqlite:///music.db')
Base.metadata.create_all(engine)
