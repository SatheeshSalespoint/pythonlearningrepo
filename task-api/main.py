from fastapi import FastAPI, Depends,HTTPException
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from models import Task
from schemas import TaskCreate, TaskResponse,TaskUpdate

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"message": "api is running!"}

# Exercise 1 — path param
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

# Exercise 2 — farewell path param
@app.get("/bye/{name}")
def say_bye(name: str):
    return {"message": f"Goodbye, {name}! See you soon."}

# Exercise 3 — two path params (int)
@app.get("/add/{a}/{b}")
def add_numbers(a: int, b: int):
    return {"a": a, "b": b, "result": a + b}

# Exercise 4 — query params with default
@app.get("/repeat")
def repeat_word(word: str, times: int = 3):
    return {"result": " ".join([word] * times)}

# Exercise 5 — path param + query param
# @app.get("/tasks/{task_id}")
# def get_task(task_id: int, status: str = "pending"):
#     return {"task_id": task_id, "status": status}

# From training — query params example
@app.get("/greet")
def greet(name: str, greeting: str = "Hello"):
    return {"message": f"{greeting}, {name}!"}

# From training — mixed path + query
@app.get("/users/{user_id}/tasks")
def get_user_tasks(user_id: int, status: str = "all"):
    return {"user": user_id, "filter": status}


# using db sessions. 

# Added description when creating a task
@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db:Session = Depends(get_db)):
    new_task = Task(title=task.title, status= task.status, description = task.description)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

# Filter tasks by status
@app.get("/tasks", response_model= list[TaskResponse])
def get_task(db:Session = Depends(get_db),status : str = None):
     if status:
         tasks = db.query(Task).filter(Task.status == status).all()
     else:
         tasks = db.query(Task).all()
     return tasks

# Return task count
@app.get("/tasks/count")
def get_count(db:Session = Depends(get_db)):
    tasks= db.query(Task).all()
    return {"count" : len(tasks)}

@app.get("/tasks/{task_id}", response_model= TaskResponse)
def get_task(task_id : int, db:Session = Depends(get_db)):
    task=  db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code= 404, detail= "Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updates: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code= 404, detail="Task not found")
    if updates.title is not None:
        task.title= updates.title
    if updates.status is not None:
        task.status= updates.status
    if updates.description is not None:
        task.description = updates.description

    db.commit()
    db.refresh(task)
    return task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
 
    db.delete(task)
    db.commit()
    return {"message": f"Task {task_id} deleted successfully"}







    
