from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

database_url= "sqlite:///./tasks.db"
engine= create_engine(database_url,connect_args={"check_same_thread":False})
session_local = sessionmaker(autocommit=False, autoflush=False,bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db= session_local()
    try:
        yield db
    finally:
        db.close()