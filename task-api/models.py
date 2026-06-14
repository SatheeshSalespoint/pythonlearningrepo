from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database import Base
from datetime import datetime

class Task(Base):
    __tablename__="tasks"
    id = Column(Integer,primary_key=True,index=True)
    title= Column(String,nullable=False)
    description= Column(String, nullable=True)
    status= Column(String, default="pending")
    is_done= Column(Boolean,default=False)
    created_at= Column(DateTime, default=datetime.utcnow)
