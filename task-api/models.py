from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
from datetime import datetime


class Task(Base):
    """SQLAlchemy ORM model — maps to the 'tasks' table in the SQLite database."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)          # auto-increment PK
    title = Column(String, nullable=False)                       # required
    description = Column(String, nullable=True)                  # optional
    status = Column(String, default="pending")                   # pending / in-progress / done
    is_done = Column(Boolean, default=False)                     # convenience boolean flag
    created_at = Column(DateTime, default=datetime.utcnow)       # set automatically on insert
