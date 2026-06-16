from pydantic import BaseModel

class TaskCreate(BaseModel):
    title:str
    status:str = "pending"
    description:str | None = None

class TaskResponse(TaskCreate):
    id:int   
    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title:str | None    = None
    status:str| None = None
    description:str | None = None

