# Day 8 — Advanced Validation & Error Handling

## Goal
Learn how to customize error responses and add middleware to your FastAPI application.

---

## Part 1 — Custom Exception Handlers (1.5 hrs)

### What You'll Learn
In C#, you use `IExceptionFilter` or middleware to customize error responses. In FastAPI, you use **exception handlers** to change how 422, 400, 404, and other errors are formatted.

### Topics
- Change the default 422 Pydantic validation error format
- Create a consistent error response shape (like C# ProblemDetails)
- Handle custom exceptions globally

### Exercise 1 — Custom 422 Handler
Right now, Pydantic returns errors in this format:
```json
{
  "detail": [
    { "loc": ["body", "title"], "msg": "String should have at least 10 characters" }
  ]
}
```

Create a custom handler to return errors in a simpler format:
```json
{
  "success": false,
  "errors": {
    "title": "String should have at least 10 characters"
  }
}
```

**Steps:**
1. Import `@app.exception_handler` from FastAPI
2. Import `RequestValidationError` from `fastapi.exceptions`
3. Create a custom handler function
4. Return a `JSONResponse` with your custom format

**Test:**
- Send `POST /tasks` with `{ "title": "Hi" }`
- Verify the new error format

---

### Exercise 2 — Custom Business Rule Exception
Create a custom exception class for business rules (instead of generic `HTTPException`).

```python
class BusinessRuleError(Exception):
    def __init__(self, message: str):
        self.message = message
```

Add a global handler that returns:
```json
{
  "success": false,
  "error": "Business rule violation",
  "message": "Tasks with 'urgent' in the title must have status 'in-progress'"
}
```

**Test:**
- Change your `validate_urgent_tasks` dependency to raise `BusinessRuleError`
- Verify the custom error format

---

## Part 2 — Middleware (1.5 hrs)

### What You'll Learn
Middleware in FastAPI = `app.UseMiddleware<>` in C# ASP.NET. It wraps every request/response and can:
- Log request/response details
- Add custom headers
- Measure request duration
- Handle CORS

### Exercise 3 — Request Logging Middleware
Create middleware that logs:
- HTTP method and path
- Request duration (in milliseconds)
- Response status code

Example output:
```
POST /tasks - 201 - 45ms
GET /tasks - 200 - 12ms
```

**Steps:**
1. Use `@app.middleware("http")`
2. Capture start time
3. Call `await call_next(request)` to pass to the endpoint
4. Capture end time and calculate duration
5. Print the log line

**Test:**
- Make several API calls
- Check the console logs

---

### Exercise 4 — Custom Response Header
Add a middleware that adds a custom header to every response:
```
X-Request-ID: <random-uuid>
```

This is useful for request tracing (like correlation IDs in distributed systems).

**Steps:**
1. Import `uuid` module
2. Generate a UUID at the start of each request
3. Add it as a response header
4. Optionally: also add it to logs for correlation

**Test:**
- Call any endpoint
- Check response headers in Postman — you should see `X-Request-ID`

---

## Part 3 — Combining Everything (1 hr)

### Exercise 5 — Full Pipeline Test
Create a single request that goes through the entire validation pipeline:

1. **Pydantic validation** — Field and model validators
2. **Business rule dependency** — Depends() check
3. **Middleware** — Logging and custom headers
4. **Custom exception handler** — If it fails

**Test scenario:**
```
POST /tasks
{
  "title": "urgent: fix bug",
  "status": "pending",
  "description": "critical issue"
}
```

Expected flow:
1. ✅ Pydantic validates: title length OK, status valid
2. ✅ @model_validator: status=pending but description provided, OK
3. ❌ Dependency: "urgent" + "pending" → triggers business rule
4. 🔧 Custom exception handler formats the error
5. 🔧 Middleware logs: "POST /tasks - 400 - Xms"
6. 🔧 Response includes X-Request-ID header

Observe the full pipeline in action!

---

## Reflection Questions

After completing Day 8, answer:

1. **What's the difference between Pydantic validators and Dependencies?**

2. **When would you use middleware vs exception handlers?**

3. **How does FastAPI's validation pipeline compare to C# ASP.NET Core?**

---

## Bonus Challenge 🌟

Add **request rate limiting** using middleware:
- Track requests per IP address
- Return `429 Too Many Requests` if > 10 requests in 60 seconds
- Use a simple in-memory dictionary (for production, use Redis)

---

## C# Comparison Reference

| FastAPI Concept | C# ASP.NET Core Equivalent |
|----------------|---------------------------|
| `@app.exception_handler` | `IExceptionFilter`, `UseExceptionHandler()` |
| `@app.middleware("http")` | `app.UseMiddleware<CustomMiddleware>()` |
| `RequestValidationError` | `ModelState.IsValid`, validation errors |
| `JSONResponse` | `return new JsonResult(...)` |
| Custom exception + handler | Custom exception + `IExceptionFilter` |
| Middleware `call_next()` | `await next.Invoke(context)` in middleware |
| Request/Response modification | `HttpContext.Request/Response` modification |

---

**Time Estimate:** 3–4 hours total  
**Prerequisites:** Completed Day 7 validation exercises

🎯 **Goal:** Master the full request/response pipeline in FastAPI!
