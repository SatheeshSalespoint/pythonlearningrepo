# 7-Day Python + FastAPI Learning Schedule

**Goal:** Build a Task Management API with FastAPI + SQLite + SQLAlchemy  
**Daily Time:** 3–4 hours | **Pace:** Slow & steady — understanding over speed

---

## Day 1 — Python Basics (3.5 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:45 | Variables, data types (int, str, float, bool) |
| 0:45 – 1:30 | `if/else` conditions and `for`/`while` loops |
| 1:30 – 2:00 | ☕ Break + quick recap |
| 2:00 – 2:45 | Functions — define, call, return values |
| 2:45 – 3:30 | 🏋️ Exercise: Write a function that filters a list of tasks by status |

---

## Day 2 — Python Intermediate (3.5 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 1 + fix any questions |
| 0:30 – 1:15 | Lists and Dictionaries |
| 1:15 – 2:00 | Classes and Objects (OOP basics) |
| 2:00 – 2:30 | ☕ Break + quick recap |
| 2:30 – 3:00 | Modules and imports |
| 3:00 – 3:30 | 🏋️ Exercise: Create a `Task` class with title, status, and a display method |

---

## Day 3 — FastAPI Introduction (4 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 2 + fix any questions |
| 0:30 – 1:15 | Install FastAPI + Uvicorn, project setup |
| 1:15 – 2:00 | Create first `GET` endpoint, understand decorators |
| 2:00 – 2:30 | ☕ Break + quick recap |
| 2:30 – 3:15 | Path params and query params |
| 3:15 – 4:00 | 🏋️ Exercise: Build a `/hello/{name}` endpoint and test in browser |

---

## Day 4 — SQLite + SQLAlchemy (4 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 3 + fix any questions |
| 0:30 – 1:15 | What is SQLAlchemy ORM? (concept + comparison to .NET Entity Framework) |
| 1:15 – 2:00 | Connect SQLite database to FastAPI |
| 2:00 – 2:30 | ☕ Break + quick recap |
| 2:30 – 3:15 | Define `Task` model with SQLAlchemy |
| 3:15 – 4:00 | 🏋️ Exercise: Create the DB and verify `tasks` table exists |

---

## Day 5 — CRUD Part 1: Create & Read (4 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 4 + fix any questions |
| 0:30 – 1:15 | Pydantic schemas — what they are and why they matter |
| 1:15 – 2:00 | `POST /tasks` — create a task and save to DB |
| 2:00 – 2:30 | ☕ Break + quick recap |
| 2:30 – 3:15 | `GET /tasks` and `GET /tasks/{id}` |
| 3:15 – 4:00 | 🏋️ Exercise: Test all 3 endpoints in Swagger UI (`/docs`) |

---

## Day 6 — CRUD Part 2: Update & Delete (4 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 5 + fix any questions |
| 0:30 – 1:15 | `PUT /tasks/{id}` — update a task |
| 1:15 – 2:00 | `DELETE /tasks/{id}` — delete a task |
| 2:00 – 2:30 | ☕ Break + quick recap |
| 2:30 – 3:15 | Error handling — return proper 404 responses |
| 3:15 – 4:00 | 🏋️ Exercise: Test all 5 CRUD endpoints end-to-end |

---

## Day 7 — Polish & Review (3.5 hrs)

| Time | Activity |
|------|----------|
| 0:00 – 0:45 | Review all 6 days — revisit anything unclear |
| 0:45 – 1:30 | Clean up project structure and add code comments |
| 1:30 – 2:00 | ☕ Break |
| 2:00 – 3:00 | Final test — run the full API, test every endpoint |
| 3:00 – 3:30 | 🎉 Celebrate! You built a Task Management API from scratch! |
