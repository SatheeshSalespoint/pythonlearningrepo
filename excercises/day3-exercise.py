"""
Day 3 Exercises — FastAPI Path & Query Parameters
==================================================
Run from task-api/ folder:
    uv run uvicorn excercises.day3-exercise:app --reload

Or copy each exercise into task-api/main.py and test there.
"""

from fastapi import FastAPI

app = FastAPI()


# Exercise 1 ✅ — Hello path param
# URL: /hello/Satheesh
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}


# Exercise 2 ✅ — Farewell path param
# URL: /bye/Satheesh
@app.get("/bye/{name}")
def say_bye(name: str):
    return {"message": f"Goodbye, {name}! See you soon."}


# Exercise 3 ✅ — Add two numbers (multiple path params, int)
# URL: /add/3/5
@app.get("/add/{a}/{b}")
def add_numbers(a: int, b: int):
    return {"a": a, "b": b, "result": a + b}


# Exercise 4 ✅ — Repeat a word (query params with default)
# URL: /repeat?word=hello  OR  /repeat?word=hello&times=2
@app.get("/repeat")
def repeat_word(word: str, times: int = 3):
    return {"result": " ".join([word] * times)}


# Exercise 5 ✅ — Task info (path param + optional query param)
# URL: /tasks/1  OR  /tasks/1?status=done
@app.get("/tasks/{task_id}")
def get_task(task_id: int, status: str = "pending"):
    return {"task_id": task_id, "status": status}
