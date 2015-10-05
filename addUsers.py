from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Users

engine = create_engine('sqlite:///music.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


User1 = Users(name="Matt Ellis",email="mellis.test@gmail.com")
session.add(User1)


session.commit()
