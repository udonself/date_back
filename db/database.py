import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from db.models import Base


load_dotenv()


engine = create_engine(os.getenv('CONNECTION_STRING'))
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)


def get_db():
    session = Session()
    return session


def depends_db():
    session = Session()
    try:
        yield session
    finally:
        session.close()