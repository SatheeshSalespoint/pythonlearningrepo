from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite database file stored locally (/// = relative path)
DATABASE_URL = "sqlite:///./tasks.db"

# check_same_thread=False is required for SQLite to work with FastAPI's async nature
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Factory that creates new DB sessions on demand
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class that all SQLAlchemy models inherit from."""
    pass


def get_db():
    """
    Dependency that provides a DB session to each endpoint.
    yield pauses here — gives the session to the endpoint — then resumes to close it.
    This ensures the session is always closed, even if an error occurs.
    """
    db = session_local()
    try:
        yield db
    finally:
        db.close()