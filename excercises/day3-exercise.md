# Day 3 Exercise — Hello Endpoint

## Task
Build a `/hello/{name}` FastAPI endpoint.

## Instructions
1. Create a new file `main.py` (or use existing one in `task-api/`)
2. Add a `GET /hello/{name}` endpoint
3. It should return a JSON response: `{"message": "Hello, <name>!"}`
4. Run the server and test it in your browser at `http://127.0.0.1:8000/hello/YourName`
5. Also open Swagger UI at `http://127.0.0.1:8000/docs` and test from there

## Starter Code
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello/{name}")
def say_hello(name: str):
    # Your code here
    pass
```

## Run the server
```bash
uvicorn main:app --reload
```

## Expected Response
```json
{
  "message": "Hello, Satheesh!"
}
```

## Your Solution
_(write your solution below)_

```python

```
