# 📊 Learning Progress Tracker

**Goal:** Task Management API with FastAPI + SQLite + SQLAlchemy  
**Start Date:** 2026-06-09  
**Target End Date:** 2026-06-15

---

## Daily Progress

| Day | Topic | Status | Date Completed | Notes / Struggles |
|-----|-------|--------|---------------|-------------------|
| Day 1 | Python Basics | ✅ Done | 2026-06-09 | Covered variables, loops, functions, data structures (tuple, set, stack, queue, generator) |
| Day 2 | Python Intermediate | ✅ Done | 2026-06-10 | Lists & Dicts, Classes & OOP, Modules & Imports. Practised inheritance, composition, namedtuple, datetime, own modules |
| Day 3 | FastAPI Introduction | ✅ Done | 2026-06-11 | Built GET endpoints, path params, query params, mixed params. Fixed: return dict not string, avoid duplicate endpoints, remove unreachable `pass` after return |
| Day 4 | SQLite + SQLAlchemy | ✅ Done | 2026-06-12 | Installed SQLAlchemy. Created database.py (engine, SessionLocal, get_db with yield). Created models.py (Task with 5 columns: id, title, description, is_done, created_at). Learnt: ORM concept, Column types, nullable vs default, index, sessions, Depends injection pattern, Alembic for migrations. Verified table in DB Browser |
| Day 5 | CRUD Part 1: Create & Read | ✅ Done | 2026-06-15 | Created schemas.py (Pydantic DTOs). Implemented POST /tasks, GET /tasks, GET /tasks/{id}. Bonus: status filter, description field, task count endpoint. Learnt: Pydantic vs SQLAlchemy models, response_model, db.query chain, endpoint order matters, no duplicate routes |
| Day 6 | CRUD Part 2: Update & Delete | ✅ Done | 2026-06-16 | Implemented PUT /tasks/{id} and DELETE /tasks/{id}. Added TaskUpdate schema (all optional fields). Error handling with 404. Removed duplicate GET /tasks endpoint. |
| Day 7 | Input Validation & Pipeline | ✅ Done | 2026-06-17 | Learned Pydantic validation (Field constraints, @field_validator, @model_validator) and FastAPI dependency injection (Depends()) for business rules. Compared to C# DataAnnotations and ActionFilters. Cleaned up code with docstrings. Validation topics: min/max length, custom validators, cross-field validation, business rules in dependencies. Key insight: Response schemas shouldn't inherit input validation rules. |
| Day 8 | Exception Handlers & Middleware | ⬜ Not Started | | Custom error responses, middleware for logging/headers, full request pipeline |

**Status Legend:**  
⬜ Not Started &nbsp;|&nbsp; 🔄 In Progress &nbsp;|&nbsp; ✅ Done &nbsp;|&nbsp; 🔁 Needs Revisit

---

## Exercise Tracker

| Day | Exercise | Completed | Comments |
|-----|----------|-----------|----------|
| Day 1 | Filter tasks by status (function) | ✅ | Used for loop, while loop, and explored tuple, set, stack, queue, generator. Minor fixes: `{}` vs `set()`, dict key access `task["status"]` |
| Day 2 | `Task` class with title, status, display | ✅ | Completed OOP exercises — `__init__`, `__str__`, inheritance (`UrgentTask`), composition (`TaskList`). Minor fixes: `super()` needs `()`, `Task4` not `Task` for class variable |
| Day 3 | `/hello/{name}` endpoint | ✅ | Completed all 5 exercises — path params, int params, query params with defaults, mixed path+query. Fixed: return dict not string, duplicate endpoints, unreachable pass |
| Day 4 | Create DB and verify `tasks` table | ✅ | Ran uvicorn, tasks.db created on disk. Learnt: create_all() only creates, doesn't alter — delete db to reset during dev |
| Day 5 | Test Create & Read in Swagger UI | ✅ | Tested POST /tasks, GET /tasks, GET /tasks/{id}, GET /tasks/count, GET /tasks?status=pending in Swagger UI and Postman. Fixed: duplicate endpoints, `description: str = True` typo, response_model can't be a dict, don't call endpoint functions directly |
| Day 6 | Test all 5 CRUD endpoints | ✅ | Tested POST, GET, GET by ID, PUT (partial update), DELETE. Verified 404 on deleted task. |
| Day 7 | Pydantic validation exercises | ✅ | Completed: Field(min_length, max_length) on title; @field_validator for status enum; @model_validator for "done requires description"; Depends() for "urgent tasks must be in-progress". Tested all scenarios in Postman. Learned validation pipeline order: Pydantic (422) → Dependencies (400/custom) → Endpoint |
| Day 8 | Exception handlers & middleware | ⬜ | Custom 422 format, BusinessRuleError exception, request logging middleware, X-Request-ID headers, full pipeline test |

---

## Concepts I Found Difficult
> Use this section to note topics you want to revisit

- `DeclarativeBase` spelling — `Declarative` not `Declartive`
- `Column` is capitalised — it's a SQLAlchemy class, not Python built-in
- SQLite URL needs 3 slashes: `sqlite:///./tasks.db`
- `yield` in `get_db()` — pauses after giving session, resumes to close it after endpoint finishes
- Python is case-sensitive everywhere — `Column` ≠ `column`
- Dictionary key access: use `task["status"]` not `task.status`
- `super()` needs `()` — use `super().__init__()` not `super.__init__()`
- strftime format codes: `%m` = month, `%d` = day (case-sensitive — `%M` = minutes!)
- `response_model` only accepts Pydantic model classes — never plain dicts
- Endpoint order matters — specific routes (e.g. `/tasks/count`) must come before dynamic ones (`/tasks/{id}`)
- Don't call endpoint functions directly from other endpoints — query the DB directly instead
- Pydantic schema = DTO (like C# AutoMapper), SQLAlchemy model = Entity (like EF Core)
- `str | None = None` means optional nullable field (like `string?` in C#)
- `Field()` in Pydantic = C# DataAnnotations (`[StringLength]`, `[Range]`)
- `@field_validator` = C# custom validation logic (like `IValidatableObject`)
- `@model_validator(mode='after')` = cross-field validation (entire object validation)
- Response schemas shouldn't inherit from input schemas — keeps validation separate
- `Depends()` = C# `ActionFilter` / dependency injection — runs after Pydantic validation
- Validation pipeline: Pydantic validators (422) → Dependencies (custom status) → Endpoint
- `is` checks object identity, `==` checks value equality — use `==` for strings
- In Python, validators must be @classmethod and return the value/object

---

## Overall Progress

- [x] Day 1 Complete
- [x] Day 2 Complete
- [x] Day 3 Complete
- [x] Day 4 Complete
- [x] Day 5 Complete
- [x] Day 6 Complete
- [x] Day 7 Complete — 🎉 **Input Validation Mastered!**
- [ ] Day 8 Complete — Advanced Pipeline & Error Handling
