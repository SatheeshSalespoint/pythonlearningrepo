from pydantic import BaseModel, Field,field_validator,model_validator

# Pydantic schemas act as DTOs (like AutoMapper in C#) — they define what data
# comes IN from requests and goes OUT in responses. They are separate from the
# SQLAlchemy model (which maps to the DB table).

VALID_STATUSES = ["pending", "in-progress", "done"]
 
def validate_status(value):
     if value is None:
         return value
     if value not in VALID_STATUSES:
         raise ValueError(f"status must be one of: {VALID_STATUSES}")
     return value



class TaskCreate(BaseModel):
    """Fields required (or optional) when creating a new task."""
    title: str = Field(min_length=10,max_length=100, description="title must have 10-100 chars")
    status: str = "pending"
    description: str | None = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, value):
        return validate_status(value)
    
    @model_validator(mode='after')
    @classmethod
    def check_done_requires_description(cls, values):
        # 'values' is the whole object with all fields
        if values.status == "done" and values.description is None or values.description == "":
            raise ValueError("Tasks marked as 'done' must have a description")
        return values  # always return the whole object

class TaskResponse(BaseModel):
    """What the API returns — extends TaskCreate and adds the DB-generated id."""
    id: int
    title: str
    status: str
    description: str | None = None
 
    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    """
    Fields that can be updated. All are optional so callers can do partial updates
    (like PATCH behaviour) — only fields provided in the request body are changed. 
       
    """
    
    title: str | None = Field(default=None, min_length=10, max_length=100)     
    status: str | None = None
    description: str | None = None

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, value):
        return validate_status(value)



   
