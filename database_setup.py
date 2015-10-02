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
    artists = Column(String(250), nullable=False)
    release_date = Column(Date)
    label = Column(String(50))
    catalog_number = Column(String(30))
    barcode = Column(String(30))
    mbid = Column(Integer)
    format = Column(String(30))
    

engine = create_engine('sqlite:///gifts.db')
Base.metadata.create_all(engine)
