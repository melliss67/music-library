from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, PageMe

engine = create_engine('sqlite:///music.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


for current in range (1, 999):
    curName = "Record: %i" % current
    print curName
    pageMeRec = PageMe(name=curName)
    session.add(pageMeRec)
    session.commit()
