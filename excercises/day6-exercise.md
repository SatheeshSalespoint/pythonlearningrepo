# Day 6 Exercise — Test All 5 CRUD Endpoints

## Task
Implement `PUT /tasks/{id}` and `DELETE /tasks/{id}`, add 404 error handling, and test all 5 endpoints.

## Instructions
1. Add Update and Delete endpoints
2. Return a proper `404` response if a task is not found
3. Test all 5 endpoints in Swagger UI (`/docs`)

## Starter Code

**main.py endpoints**
```python
from fastapi import HTTPException

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updated: TaskCreate, db: Session = Depends(get_db)):
    # Your code here
    # Hint: fetch task, update fields, commit, return updated task
    # If not found, raise HTTPException(status_code=404, detail="Task not found")
    pass

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    # Your code here
    # Hint: fetch task, delete, commit, return confirmation message
    # If not found, raise HTTPException(status_code=404, detail="Task not found")
    pass
```

## End-to-End Test Checklist
Test each of these in Swagger UI:

- [ ] `POST /tasks` — create a task
- [ ] `GET /tasks` — list all tasks
- [ ] `GET /tasks/{id}` — get one task
- [ ] `PUT /tasks/{id}` — update task status to `"done"`
- [ ] `DELETE /tasks/{id}` — delete a task
- [ ] `GET /tasks/{id}` with a non-existent ID — should return `404`

## Your Notes
_(write observations or issues below)_

```

```
