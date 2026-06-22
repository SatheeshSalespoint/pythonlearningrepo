from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException,RequestValidationError
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate
import time
import uuid


class BusinessRuleError(Exception):
     """Raised when a business rule is violated."""
     def __init__(self, message: str):
         self.message = message

app = FastAPI(title="Task Management API", description="A simple CRUD API for managing tasks", version="1.0.0")

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
             "success": False,
             "status_code": exc.status_code,
             "message": exc.detail
         }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = exc.errors()
    first_error = errors[0]
    field = first_error["loc"][-1]   
    message = first_error["msg"]     
 
    return JSONResponse(
         status_code=422,
         content={
             "success": False,
             "status_code": 422,
             "message": f"{field}: {message}"
         }
    )

@app.exception_handler(BusinessRuleError)
async def business_rule_exception_handler(request, exc):
     return JSONResponse(
         status_code=400,
         content={
             "success": False,
             "status_code": 400,
             "message": exc.message
         }
     )

@app.middleware("http")
async def logging_middleware(request, call_next):
     request_id = str(uuid.uuid4())
     start_time = time.time()
 
     # â everything above here runs BEFORE the endpoint
     response = await call_next(request)
     # â everything below here runs AFTER the endpoint
     response.headers["X-Request-ID"] = request_id
 
     duration_ms = (time.time() - start_time) * 1000
     print(f"â {request.method} {request.url.path} â {response.status_code} | {duration_ms:.2f}ms")
    
     return response
     

# Create all database tables on startup (safe to call multiple times — only creates if not exists)
Base.metadata.create_all(bind=engine)


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/")
def health():
    """Simple health check to confirm the API is running."""
    return {"message": "api is running!"}


# ── Task Endpoints ────────────────────────────────────────────────────────────

def validate_urgent_tasks(task: TaskCreate):
     """Business rule: urgent tasks must be in-progress"""
     if "urgent" in task.title.lower() and task.status == "pending":
          raise BusinessRuleError("Tasks with 'urgent' in the title must have status 'in-progress'")
        #  raise HTTPException(
        #      status_code=400, 
        #      detail="Tasks with 'urgent' in the title must have status 'in-progress'"
        #  )
     return task


@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate = Depends(validate_urgent_tasks), db: Session = Depends(get_db)):
    """Create a new task and save it to the database."""
    new_task = Task(title=task.title, status=task.status, description=task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)  # reload from DB to get auto-generated id and created_at
    return new_task


@app.get("/tasks/count")
def get_task_count(db: Session = Depends(get_db)):
    """Return the total number of tasks in the database."""
    count = db.query(Task).count()
    return {"count": count}


# NOTE: /tasks/count must come BEFORE /tasks/{task_id}, otherwise "count" would be
# treated as a task_id (a string passed to an int param → 422 error).
@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db), status: str = None):
    """
    List all tasks. Optionally filter by status.
    Example: GET /tasks?status=pending
    """
    if status:
        return db.query(Task).filter(Task.status == status).all()
    return db.query(Task).all()


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by its ID. Returns 404 if not found."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updates: TaskUpdate, db: Session = Depends(get_db)):
    """
    Update an existing task. Only fields provided in the request body are changed
    (partial update — all fields in TaskUpdate are optional).
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if updates.title is not None:
        task.title = updates.title
    if updates.status is not None:
        task.status = updates.status
    if updates.description is not None:
        task.description = updates.description

    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task by ID. Returns 404 if not found."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"message": f"Task {task_id} deleted successfully"}







    
