# =============================================================================
# Day 11 — Calling External APIs with Python
# Goal: Use the requests library to call real APIs and handle responses
# =============================================================================

import requests
import json

print("=" * 60)
print("BLOCK 1 — GET Requests")
print("=" * 60)

# The requests library lets you call any HTTP API — just like
# Postman or your browser, but from Python code.

# --- Simple GET request ---
# We'll use JSONPlaceholder — a free fake REST API for practice
url = "https://jsonplaceholder.typicode.com/todos/1"

response = requests.get(url)

print(f"\nURL: {url}")
print(f"Status code: {response.status_code}")   # 200 = OK, 404 = Not Found etc.
print(f"Response type: {type(response)}")

# --- Reading the response body ---
# .text  = raw string
# .json() = parsed Python dict (only works if response is JSON)
print(f"\nRaw text:\n{response.text}")
print(f"\nParsed as dict:\n{response.json()}")

data = response.json()
print(f"\nAccessing fields:")
print(f"  ID:        {data['id']}")
print(f"  Title:     {data['title']}")
print(f"  Completed: {data['completed']}")

# --- GET with query parameters ---
# Query params are key=value pairs after ? in the URL
# e.g. /todos?userId=1&completed=true
print("\n" + "-" * 40)
print("GET with query parameters")
print("-" * 40)

params = {"userId": 1, "_limit": 3}   # requests builds ?userId=1&_limit=3
response2 = requests.get("https://jsonplaceholder.typicode.com/todos", params=params)

print(f"Status: {response2.status_code}")
todos = response2.json()
print(f"Got {len(todos)} todos:")
for todo in todos:
    status = "done" if todo["completed"] else "pending"
    print(f"  [{status}] {todo['title']}")


print("\n" + "=" * 60)
print("BLOCK 2 — POST Requests + Status Codes")
print("=" * 60)

# POST sends data to the server (like creating a new record)
# In C# this is like HttpClient.PostAsync() with a JSON body

new_task = {
    "title": "Learn Python APIs",
    "body":  "Using the requests library",
    "userId": 1,
}

post_response = requests.post(
    "https://jsonplaceholder.typicode.com/posts",
    json=new_task    # automatically sets Content-Type: application/json
)

print(f"\nPOST status: {post_response.status_code}")   # 201 = Created
print(f"Created resource: {post_response.json()}")

# --- Understanding status codes ---
print("\n" + "-" * 40)
print("Status Codes")
print("-" * 40)
print("  2xx = Success  (200 OK, 201 Created, 204 No Content)")
print("  4xx = Client error (400 Bad Request, 401 Unauth, 404 Not Found)")
print("  5xx = Server error (500 Internal Server Error)")

# Check status in code
r = requests.get("https://jsonplaceholder.typicode.com/todos/1")
if r.status_code == 200:
    print(f"\n200 OK — data received")
elif r.status_code == 404:
    print(f"\n404 — resource not found")

# response.ok = True if status < 400 (convenient shortcut)
print(f"response.ok: {r.ok}")

# --- Response headers ---
print(f"\nContent-Type header: {r.headers.get('Content-Type')}")


print("\n" + "=" * 60)
print("BLOCK 3 — Error Handling with try/except")
print("=" * 60)

# APIs can fail — network error, timeout, bad URL etc.
# Always wrap API calls in try/except in production code

# --- Basic try/except ---
try:
    r = requests.get("https://jsonplaceholder.typicode.com/todos/1", timeout=5)
    r.raise_for_status()   # raises an exception if status >= 400
    print(f"Success: {r.json()['title']}")
except requests.exceptions.Timeout:
    print("Error: Request timed out")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to server")
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e}")
except requests.exceptions.RequestException as e:
    # Catches ANY requests error — use as a catch-all
    print(f"Request failed: {e}")

# --- Simulating a 404 ---
print("\nTrying a non-existent resource:")
try:
    r = requests.get("https://jsonplaceholder.typicode.com/todos/99999", timeout=5)
    r.raise_for_status()
    print(r.json())
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error caught: {e}")

# --- Helper function pattern (how you'd write it in real code) ---
print("\n" + "-" * 40)
print("Reusable API call function")
print("-" * 40)

def get_todo(todo_id: int) -> dict | None:
    """Fetch a single todo by ID. Returns dict or None on failure."""
    try:
        r = requests.get(
            f"https://jsonplaceholder.typicode.com/todos/{todo_id}",
            timeout=5
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch todo {todo_id}: {e}")
        return None

todo = get_todo(5)
if todo:
    print(f"Todo 5: {todo['title']}")

missing = get_todo(99999)
print(f"Todo 99999: {missing}")   # None


print("\n" + "=" * 60)
print("BLOCK 4 — API Keys and .env files")
print("=" * 60)

# Real APIs require an API key for authentication.
# NEVER hardcode keys in your source code — use .env files instead.

# --- Why .env? ---
# Bad (exposed in git history):
#   API_KEY = "sk-abc123secret"
#
# Good — store in .env file (which is git-ignored):
#   API_KEY=sk-abc123secret
#
# Then load it in Python:
from dotenv import load_dotenv
import os

load_dotenv()   # reads .env file from current directory into os.environ

api_key = os.getenv("API_KEY", "not-set")   # second arg = default if missing
print(f"\nAPI_KEY from .env: {api_key}")

# --- How to use a key in a request ---
# Most APIs accept the key in one of these ways:

# Option 1: Query parameter
# requests.get(url, params={"api_key": api_key})

# Option 2: Header (most common — Bearer token)
# requests.get(url, headers={"Authorization": f"Bearer {api_key}"})

# Option 3: Header (X-API-Key style)
# requests.get(url, headers={"X-API-Key": api_key})

print("\nAPI key patterns:")
print("  params={'api_key': key}                       # query param")
print("  headers={'Authorization': f'Bearer {key}'}   # Bearer token")
print("  headers={'X-API-Key': key}                   # custom header")

print("\nDay 11 Basics complete!")
print("Now move on to the exercise: day11_api_exercise.py")
