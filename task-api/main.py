from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Task
from schemas import TaskCreate, TaskResponse, TaskUpdate

app = FastAPI(title="Task Management API", description="A simple CRUD API for managing tasks", version="1.0.0")

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
         raise HTTPException(
             status_code=400, 
             detail="Tasks with 'urgent' in the title must have status 'in-progress'"
         )
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







    
