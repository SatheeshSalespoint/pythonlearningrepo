# Python + FastAPI + AI Learning Schedule

**Ultimate Goal:** Become an AI Engineer (3-month plan)  
**Daily Time:** 3–4 hours | **Pace:** Slow & steady — understanding over speed

---

# Phase 1 — Python + FastAPI ✅ COMPLETED (Days 1–8)

---

# Phase 2 — Python for Data & AI APIs (Days 9–15)

**Goal:** Understand data tools and call real AI services  
**Start Date:** 2026-06-24

---

## Day 9 — NumPy Basics (3.5 hrs)
> *Why: Everything in AI/ML is arrays and numbers. NumPy is the foundation.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | What is NumPy? Why AI needs arrays (vs Python lists) |
| 0:30 – 1:15 | Creating arrays — `np.array()`, `np.zeros()`, `np.ones()`, `np.arange()` |
| 1:15 – 2:00 | Array operations — math, slicing, reshaping |
| 2:00 – 2:30 | ☕ Break + recap |
| 2:30 – 3:15 | Array aggregations — `sum`, `mean`, `max`, `min`, `std` |
| 3:15 – 3:30 | 🏋️ Exercise: Create a score array, calculate average, find highest score |

---

## Day 10 — Pandas Basics (4 hrs)
> *Why: Every AI project starts with data. Pandas is how you load, clean and explore it.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 9 + fix questions |
| 0:30 – 1:15 | What is a DataFrame? (like a database table in Python) |
| 1:15 – 2:00 | Reading CSV files, exploring data — `head()`, `info()`, `describe()` |
| 2:00 – 2:30 | ☕ Break + recap |
| 2:30 – 3:15 | Filtering, selecting columns, handling missing values |
| 3:15 – 4:00 | 🏋️ Exercise: Load a tasks CSV, filter by status, find most common task |

---

## Day 11 — Calling External APIs with Python (3.5 hrs)
> *Why: AI engineering = calling AI services over HTTP. Learn the `requests` library + error handling.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 10 + fix questions |
| 0:30 – 1:00 | `requests` library — GET and POST requests in Python |
| 1:00 – 1:45 | Handling responses — JSON parsing, status codes, `try/except` |
| 1:45 – 2:15 | ☕ Break + recap |
| 2:15 – 3:00 | API keys — what they are, how to store them safely (`.env` + `python-dotenv`) |
| 3:00 – 3:30 | 🏋️ Exercise: Call a free public API, parse the response, print results |

---

## Day 12 — OpenAI API Basics (4 hrs)
> *Why: Your first real AI integration. Understanding how to talk to an LLM programmatically.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 11 + fix questions |
| 0:30 – 1:00 | What is the OpenAI API? Models — GPT-4o, embeddings, tokens |
| 1:00 – 1:45 | Setup — install `openai`, configure API key, first completion call |
| 1:45 – 2:15 | ☕ Break + recap |
| 2:15 – 3:00 | Chat completions — `system`, `user`, `assistant` message roles |
| 3:00 – 4:00 | 🏋️ Exercise: Build a Python script that answers questions about your tasks |

---

## Day 13 — Prompt Engineering (3.5 hrs)
> *Why: The quality of AI output depends entirely on how you write prompts. This is a core AI engineer skill.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 12 + fix questions |
| 0:30 – 1:15 | Prompt patterns — zero-shot, few-shot, chain-of-thought |
| 1:15 – 2:00 | System prompts — giving the AI a role and constraints |
| 2:00 – 2:30 | ☕ Break + recap |
| 2:30 – 3:15 | Prompt templating — dynamic prompts with variables (f-strings) |
| 3:15 – 3:30 | 🏋️ Exercise: Write 3 prompts for a task assistant — improve output quality each time |

---

## Day 14 — LangChain Basics (4 hrs)
> *Why: LangChain is the #1 AI framework. It standardises how you build AI apps — chains, prompts, models.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 13 + fix questions |
| 0:30 – 1:15 | What is LangChain? Why use it over raw OpenAI API? |
| 1:15 – 2:00 | Core concepts — `ChatPromptTemplate`, `LLM`, `Chain` |
| 2:00 – 2:30 | ☕ Break + recap |
| 2:30 – 3:15 | Build a simple chain — prompt template → LLM → output |
| 3:15 – 4:00 | 🏋️ Exercise: Build a task summariser chain with LangChain |

---

## Day 15 — Mini Project: AI-Powered FastAPI Endpoint (4 hrs)
> *Why: Combine everything — FastAPI + OpenAI + LangChain into one real AI-powered API.*

| Time | Activity |
|------|----------|
| 0:00 – 0:30 | Recap Day 14 + fix questions |
| 0:30 – 1:15 | Design the AI endpoint — `POST /tasks/{id}/summarise` |
| 1:15 – 2:00 | Integrate OpenAI into your existing Task API |
| 2:00 – 2:30 | ☕ Break + recap |
| 2:30 – 3:15 | Add a `POST /tasks/suggest` endpoint — AI suggests task priority |
| 3:15 – 4:00 | 🏋️ Final test — run the full AI API, test every endpoint in Postman |

---

# Phase 1 — Original Schedule (Days 1–8)

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
