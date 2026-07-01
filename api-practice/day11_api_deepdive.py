# =============================================================================
# Day 11 — Deep Dive: HTTP Calls In Depth
# Topics:
#   1. All HTTP methods — GET, POST, PUT, PATCH, DELETE
#   2. Headers and authentication patterns
#   3. Error handling — retries, timeouts, all exception types
#   4. Real API practice — calling your own FastAPI Task API
# =============================================================================

import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://jsonplaceholder.typicode.com"


# =============================================================================
# PART 1 — ALL HTTP METHODS (Full CRUD over HTTP)
# =============================================================================
print("=" * 60)
print("PART 1 — All HTTP Methods")
print("=" * 60)

# HTTP methods map directly to CRUD operations:
#
#  Method  | CRUD   | SQL      | Your FastAPI
# ---------|--------|----------|------------------
#  GET     | Read   | SELECT   | GET /tasks
#  POST    | Create | INSERT   | POST /tasks
#  PUT     | Replace| UPDATE * | PUT /tasks/{id}
#  PATCH   | Partial| UPDATE   | (partial update)
#  DELETE  | Delete | DELETE   | DELETE /tasks/{id}
#
# * PUT replaces the WHOLE resource. PATCH updates only what you send.

# --- GET ---
print("\n--- GET (Read) ---")
r = requests.get(f"{BASE}/posts/1")
print(f"Status: {r.status_code}  |  Title: {r.json()['title'][:40]}...")

# --- POST (Create) ---
print("\n--- POST (Create) ---")
r = requests.post(f"{BASE}/posts", json={
    "title": "My new post",
    "body":  "Some content here",
    "userId": 1
})
print(f"Status: {r.status_code}  |  Created ID: {r.json()['id']}")

# --- PUT (Full Replace) ---
print("\n--- PUT (Full Replace) ---")
# PUT sends the ENTIRE object — missing fields get wiped
r = requests.put(f"{BASE}/posts/1", json={
    "id":     1,
    "title":  "Completely replaced title",
    "body":   "Completely replaced body",
    "userId": 1
})
print(f"Status: {r.status_code}  |  Response: {r.json()}")

# --- PATCH (Partial Update) ---
print("\n--- PATCH (Partial Update) ---")
# PATCH sends ONLY the fields you want to change
r = requests.patch(f"{BASE}/posts/1", json={
    "title": "Only title changed"
    # body and userId are untouched
})
print(f"Status: {r.status_code}  |  Response: {r.json()}")

# --- DELETE ---
print("\n--- DELETE ---")
r = requests.delete(f"{BASE}/posts/1")
print(f"Status: {r.status_code}")   # 200 on JSONPlaceholder (real APIs return 204)
# 204 = No Content — success but no body returned

# --- PUT vs PATCH — key difference ---
print("\n--- PUT vs PATCH ---")
print("PUT  — send ALL fields or missing ones get wiped/nulled")
print("PATCH — send ONLY changed fields, rest stays as-is")
print("Your FastAPI TaskUpdate schema (all Optional fields) = PATCH behaviour")


# =============================================================================
# PART 2 — HEADERS AND AUTHENTICATION
# =============================================================================
print("\n" + "=" * 60)
print("PART 2 — Headers and Authentication")
print("=" * 60)

# --- What are headers? ---
# Headers are metadata sent alongside a request — like labels on an envelope.
# Common uses: auth tokens, content type, tracing IDs, caching

# --- Viewing response headers ---
r = requests.get(f"{BASE}/posts/1")
print("\nResponse headers (key ones):")
print(f"  Content-Type:  {r.headers.get('Content-Type')}")
print(f"  Cache-Control: {r.headers.get('Cache-Control')}")
print(f"  Server:        {r.headers.get('Via')}")

# --- Sending custom request headers ---
print("\n--- Sending request headers ---")
custom_headers = {
    "Accept":        "application/json",
    "User-Agent":    "MyPythonApp/1.0",
    "X-Request-ID":  "abc-123-xyz",     # like your Day 8 middleware!
}
r = requests.get(f"{BASE}/posts/1", headers=custom_headers)
print(f"Status: {r.status_code}  (sent custom headers)")

# --- Authentication patterns ---
print("\n--- Auth Pattern 1: Bearer Token (most common for AI APIs) ---")
# Used by: OpenAI, Anthropic, Groq, GitHub API
fake_token = "sk-abc123fake"
r = requests.get(f"{BASE}/posts/1", headers={
    "Authorization": f"Bearer {fake_token}"
})
print(f"Bearer token sent — Status: {r.status_code}")

print("\n--- Auth Pattern 2: API Key in header ---")
# Used by: some weather APIs, internal APIs
r = requests.get(f"{BASE}/posts/1", headers={
    "X-API-Key": "my-api-key-here"
})
print(f"API Key header sent — Status: {r.status_code}")

print("\n--- Auth Pattern 3: API Key as query param ---")
# Used by: some older APIs (less secure — key visible in URL logs)
r = requests.get(f"{BASE}/posts/1", params={"api_key": "my-api-key-here"})
print(f"API Key in params — Status: {r.status_code}")

print("\n--- Auth Pattern 4: Basic Auth (username + password) ---")
# Used by: some legacy APIs, HTTP basic auth
r = requests.get(f"{BASE}/posts/1", auth=("username", "password"))
print(f"Basic auth sent — Status: {r.status_code}")

# --- requests.Session — reuse headers across multiple calls ---
print("\n--- Session: reuse headers across calls ---")
# Instead of passing headers to every request, attach them to a session
session = requests.Session()
session.headers.update({
    "Authorization": "Bearer my-token",
    "User-Agent":    "MyApp/1.0",
})

# All calls via session automatically include those headers
r1 = session.get(f"{BASE}/posts/1")
r2 = session.get(f"{BASE}/posts/2")
print(f"Session call 1: {r1.status_code}  |  '{r1.json()['title'][:30]}...'")
print(f"Session call 2: {r2.status_code}  |  '{r2.json()['title'][:30]}...'")
# Session also reuses TCP connections = faster for multiple calls


# =============================================================================
# PART 3 — ERROR HANDLING IN DEPTH
# =============================================================================
print("\n" + "=" * 60)
print("PART 3 — Error Handling In Depth")
print("=" * 60)

# --- All requests exception types ---
print("\n--- Exception hierarchy ---")
print("""
requests.exceptions.RequestException        (base class - catch-all)
  +-- ConnectionError                        (no network / DNS failure)
  |     +-- ProxyError
  +-- Timeout                                (request took too long)
  |     +-- ConnectTimeout                   (couldn't connect in time)
  |     +-- ReadTimeout                      (connected but no data)
  +-- URLRequired                            (invalid URL)
  +-- TooManyRedirects                       (redirect loop)
  +-- HTTPError                              (raised by raise_for_status())
        (4xx Client errors, 5xx Server errors)
""")

# --- timeout parameter in depth ---
print("--- Timeout: connect vs read ---")
# timeout=5              → 5s for both connect AND read
# timeout=(3, 10)        → 3s to connect, 10s to read response
# Always set a timeout — without it, requests can hang forever!
try:
    r = requests.get(f"{BASE}/posts/1", timeout=(3, 10))
    print(f"Got response in time: {r.status_code}")
except requests.exceptions.ConnectTimeout:
    print("Could not connect within 3 seconds")
except requests.exceptions.ReadTimeout:
    print("Connected but response took too long")

# --- raise_for_status() in depth ---
print("\n--- raise_for_status() ---")
print("200-299  = no exception raised")
print("400-499  = raises HTTPError (your bug - bad request, not found, unauth)")
print("500-599  = raises HTTPError (their bug - server error)")

try:
    r = requests.get(f"{BASE}/posts/99999")
    r.raise_for_status()
except requests.exceptions.HTTPError as e:
    print(f"HTTPError: {e}")
    print(f"Status code was: {e.response.status_code}")

# --- Retry logic with urllib3 ---
print("\n--- Automatic Retries ---")
# Retry on connection failures or 5xx server errors — not on 4xx (your fault)

retry_strategy = Retry(
    total=3,                        # max 3 retries
    backoff_factor=1,               # wait 1s, 2s, 4s between retries
    status_forcelist=[500, 502, 503, 504],  # retry on these server errors
    allowed_methods=["GET"],        # only retry GET (safe to repeat)
)
adapter = HTTPAdapter(max_retries=retry_strategy)

session_with_retry = requests.Session()
session_with_retry.mount("https://", adapter)
session_with_retry.mount("http://",  adapter)

try:
    r = session_with_retry.get(f"{BASE}/posts/1", timeout=5)
    r.raise_for_status()
    print(f"Got post with retry-enabled session: {r.status_code}")
except requests.exceptions.RequestException as e:
    print(f"All retries failed: {e}")

# --- Production-ready API call pattern ---
print("\n--- Production-ready pattern ---")

def call_api(url: str, method: str = "GET", **kwargs) -> dict | None:
    """
    Generic API caller with timeout, error handling, and status check.
    Returns parsed JSON or None on failure.
    """
    try:
        response = requests.request(method, url, timeout=(3, 10), **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectTimeout:
        print(f"Timeout connecting to {url}")
    except requests.exceptions.ReadTimeout:
        print(f"Timeout reading from {url}")
    except requests.exceptions.ConnectionError:
        print(f"Connection failed: {url}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP {e.response.status_code} from {url}: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Unexpected error: {e}")
    return None

result = call_api(f"{BASE}/posts/5")
print(f"call_api success: {result['title'][:40]}")

result = call_api(f"{BASE}/posts/99999")
print(f"call_api failure: {result}")


# =============================================================================
# PART 4 — REAL API: Call your own FastAPI Task API
# =============================================================================
print("\n" + "=" * 60)
print("PART 4 — Calling Your Own FastAPI Task API")
print("=" * 60)
print()
print("Start your FastAPI server first:")
print("  cd task-api")
print("  uv run uvicorn app.main:app --reload")
print()
print("Then run this section (uncomment the code below)")
print()

# Uncomment and run this block AFTER starting your FastAPI server:

TASK_API = "http://127.0.0.1:8000"

def check_server_running() -> bool:
    try:
        requests.get(TASK_API + "/tasks", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False

if not check_server_running():
    print("FastAPI server not running — skipping Part 4")
    print("Start it with: cd task-api && uv run uvicorn app.main:app --reload")
else:
    print("FastAPI server is running!\n")

    # --- GET all tasks ---
    print("--- GET /tasks ---")
    r = requests.get(f"{TASK_API}/tasks")
    tasks = r.json()
    print(f"Total tasks: {len(tasks)}")
    for t in tasks[:3]:
        print(f"  [{t['status']}] {t['title']}")

    # --- POST a new task ---
    print("\n--- POST /tasks ---")
    new_task = {
        "title":       "Learn HTTP from Python",
        "description": "Using the requests library",
        "status":      "in-progress"
    }
    r = requests.post(f"{TASK_API}/tasks", json=new_task)
    print(f"Status: {r.status_code}")
    created = r.json()
    task_id = created["id"]
    print(f"Created task ID: {task_id}  |  Title: {created['title']}")

    # --- GET single task ---
    print(f"\n--- GET /tasks/{task_id} ---")
    r = requests.get(f"{TASK_API}/tasks/{task_id}")
    print(f"Status: {r.status_code}  |  {r.json()}")

    # --- PUT update ---
    print(f"\n--- PUT /tasks/{task_id} ---")
    r = requests.put(f"{TASK_API}/tasks/{task_id}", json={
        "title":  "Learn HTTP from Python",
        "status": "done"
    })
    print(f"Status: {r.status_code}  |  Updated: {r.json()}")

    # --- DELETE ---
    print(f"\n--- DELETE /tasks/{task_id} ---")
    r = requests.delete(f"{TASK_API}/tasks/{task_id}")
    print(f"Status: {r.status_code}  |  Deleted: {r.json()}")

    # --- Confirm deleted (expect 404) ---
    print(f"\n--- GET /tasks/{task_id} (should 404) ---")
    r = requests.get(f"{TASK_API}/tasks/{task_id}")
    print(f"Status: {r.status_code}  |  {r.json()}")

print("\nDay 11 Deep Dive complete!")
