from fastapi import FastAPI

app = FastAPI()

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
@app.get("/tasks/{task_id}")
def get_task(task_id: int, status: str = "pending"):
    return {"task_id": task_id, "status": status}

# From training — query params example
@app.get("/greet")
def greet(name: str, greeting: str = "Hello"):
    return {"message": f"{greeting}, {name}!"}

# From training — mixed path + query
@app.get("/users/{user_id}/tasks")
def get_user_tasks(user_id: int, status: str = "all"):
    return {"user": user_id, "filter": status}
