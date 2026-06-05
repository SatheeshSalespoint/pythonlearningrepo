# Day 5 Exercise — Test Create & Read in Swagger UI

## Task
Implement `POST /tasks` and `GET /tasks` and `GET /tasks/{id}` endpoints and test them in Swagger UI.

## Instructions
1. Add Pydantic schema for task input/output
2. Implement the 3 endpoints
3. Run the server and open `http://127.0.0.1:8000/docs`
4. Create at least 2 tasks using `POST /tasks`
5. Retrieve all tasks using `GET /tasks`
6. Retrieve a single task by ID using `GET /tasks/{id}`

## Starter Code

**schemas.py**
```python
from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    status: str = "pending"

class TaskResponse(TaskCreate):
    id: int

    class Config:
        orm_mode = True
```

**main.py endpoints**
```python
@app.post("/tasks", response_model=TaskResponse)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    # Your code here
    pass

@app.get("/tasks", response_model=list[TaskResponse])
def get_tasks(db: Session = Depends(get_db)):
    # Your code here
    pass

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    # Your code here
    pass
```

## Expected Swagger Test
- `POST /tasks` → body: `{"title": "My first task", "status": "pending"}` → returns task with `id`
- `GET /tasks` → returns list of all tasks
- `GET /tasks/1` → returns the first task

## Your Notes
_(write observations or issues below)_

```

```
