# Day 7 Exercise — Full API End-to-End Test

## Task
Run the complete Task Management API and verify everything works together.

## Final Checklist

### Project Structure
Make sure your `task-api/` folder looks something like this:
```
task-api/
├── main.py         # FastAPI app + all endpoints
├── database.py     # SQLite connection
├── models.py       # SQLAlchemy Task model
├── schemas.py      # Pydantic schemas
└── tasks.db        # SQLite database (auto-created)
```

### Run the API
```bash
cd task-api
uvicorn main:app --reload
```

### End-to-End Test (Swagger UI at `/docs`)
- [ ] Create 3 tasks with different statuses
- [ ] List all tasks — confirm all 3 appear
- [ ] Get a single task by ID
- [ ] Update a task's status to `"done"`
- [ ] Delete one task
- [ ] Confirm deleted task returns `404`
- [ ] List all tasks again — confirm only 2 remain

### Reflection
Answer these after completing:

1. What was the hardest concept this week?
2. What would you do differently next time?
3. What do you want to learn next? (e.g., authentication, deployment, testing)

---
_(write your answers below)_

**Hardest concept:**  

**Would do differently:**  

**Want to learn next:**  

---

🎉 **Congratulations! You built a Task Management API in 7 days!**
