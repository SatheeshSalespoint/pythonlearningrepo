# Day 1 Exercise — Filter Tasks by Status

## Task
Write a Python function that takes a list of tasks and filters them by a given status.

## Instructions
1. Create a list of task dictionaries, each with `title` and `status` fields
2. Write a function `filter_tasks(tasks, status)` that returns only tasks matching the given status
3. Test it with statuses: `"pending"`, `"done"`, `"in-progress"`

## Starter Code
```python
tasks = [
    {"title": "Buy groceries", "status": "pending"},
    {"title": "Write report", "status": "done"},
    {"title": "Fix bug", "status": "in-progress"},
    {"title": "Send email", "status": "pending"},
]

def filter_tasks(tasks, status):
    # Your code here
    pass

# Test it
print(filter_tasks(tasks, "pending"))
```

## Expected Output
```
[{'title': 'Buy groceries', 'status': 'pending'}, {'title': 'Send email', 'status': 'pending'}]
```

## Your Solution
_(write your solution below)_

```python

```
