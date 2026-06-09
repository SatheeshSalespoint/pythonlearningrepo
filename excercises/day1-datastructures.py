# -------------------------------------------------------
# Python Data Structures — Compared with C#
# -------------------------------------------------------


# -------------------------------------------------------
# 1. TUPLE  (C# equivalent: readonly struct / ValueTuple)
# -------------------------------------------------------
# - Ordered, immutable (cannot change after creation)
# - Use when data should NOT change

task = ("Buy groceries", "pending", 1)
print(task[0])        # Buy groceries
print(task[1])        # pending
# task[0] = "x"       # ❌ Error — tuples are immutable

# Named tuple (like C# ValueTuple with named fields)
from collections import namedtuple
Task = namedtuple("Task", ["title", "status", "id"])
t = Task(title="Fix bug", status="in-progress", id=2)
print(t.title)        # Fix bug
print(t.status)       # in-progress

# Exercise 1: Create a tuple for a user (name, age, role) and print each field
# Your code here

user = ("satheesh",36, "Senior Developer")
print(user[0])
print(user[1])
print(user[2])


#namedtuple
user = namedtuple("User", ["name","age","role"])
u = user(name="satheesh",age=36,role="senior developer")
print(u.name)
print(u.age)
print(u.role)

# -------------------------------------------------------
# 2. SET  (C# equivalent: HashSet<T>)
# -------------------------------------------------------
# - Unordered, no duplicates
# - Fast lookup — use when uniqueness matters

statuses = {"pending", "done", "in-progress", "pending"}  # duplicate removed
print(statuses)       # {'pending', 'done', 'in-progress'}

# Add / Remove
statuses.add("cancelled")
statuses.discard("done")
print(statuses)

# Check membership
print("pending" in statuses)    # True
print("done" in statuses)       # False

# Set operations (like C# Intersect, Union, Except)
a = {"pending", "done"}
b = {"done", "in-progress"}
print(a | b)    # Union:        {'pending', 'done', 'in-progress'}
print(a & b)    # Intersection: {'done'}
print(a - b)    # Difference:   {'pending'}

# Exercise 2: Given a list of tasks, use a set to get all unique statuses
tasks = [
    {"title": "Buy groceries", "status": "pending"},
    {"title": "Write report", "status": "done"},
    {"title": "Fix bug", "status": "in-progress"},
    {"title": "Send email", "status": "pending"},
]
# Your code here — expected: {'pending', 'done', 'in-progress'}
result=set();
for task in tasks:
    result.add(task["status"])

print(result)


# -------------------------------------------------------
# 3. STACK  (C# equivalent: Stack<T>)
# -------------------------------------------------------
# - LIFO (Last In, First Out)
# - Python uses a plain list as a stack

stack = []
stack.append("task-1")   # Push
stack.append("task-2")   # Push
stack.append("task-3")   # Push
print(stack)             # ['task-1', 'task-2', 'task-3']

top = stack.pop()        # Pop (removes last)
print(top)               # task-3
print(stack)             # ['task-1', 'task-2']

print(stack[-1])         # Peek (view top without removing)

# Exercise 3: Push 3 tasks onto a stack, pop them one by one and print each
# Your code here
_stack=[]
_stack.append("task-1")
_stack.append("task-2")
_stack.append("task-3")

while _stack:
    _lastitem= _stack.pop()
    print(_lastitem)

# -------------------------------------------------------
# 4. QUEUE  (C# equivalent: Queue<T>)
# -------------------------------------------------------
# - FIFO (First In, First Out)
# - Use collections.deque for efficient queue

from collections import deque

queue = deque()
queue.append("task-1")     # Enqueue
queue.append("task-2")     # Enqueue
queue.append("task-3")     # Enqueue
print(queue)               # deque(['task-1', 'task-2', 'task-3'])

first = queue.popleft()    # Dequeue (removes first)
print(first)               # task-1
print(queue)               # deque(['task-2', 'task-3'])

print(queue[0])            # Peek front without removing

# Exercise 4: Simulate a task queue — enqueue 3 tasks, process (dequeue) them one by one
# Your code here
_queue =deque()
_queue.append("task-1")
_queue.append("task-2")
_queue.append("task-3")


while _queue:
    _firstitem= _queue.popleft()
    print(_firstitem)

# -------------------------------------------------------
# 5. GENERATOR  (C# equivalent: IEnumerable<T> / yield return)
# -------------------------------------------------------
# - Lazy evaluation — generates items one at a time
# - Memory efficient for large data

# C# style:
# IEnumerable<Task> GetPending() { foreach(var t in tasks) if(t.Status=="pending") yield return t; }

def get_pending(tasks):
    for task in tasks:
        if task["status"] == "pending":
            yield task          # yield = lazy return (like C# yield return)

pending_gen = get_pending(tasks)
print(next(pending_gen))    # Get first item
print(next(pending_gen))    # Get second item

# Or iterate all
for task in get_pending(tasks):
    print(task["title"])

# Generator expression (one-liner) — like LINQ IEnumerable
titles = (task["title"] for task in tasks if task["status"] == "pending")
print(list(titles))

# Exercise 5: Write a generator that yields only tasks with status "done"
# Your code here
def get_done(tasks):
    for task in tasks:
        if task["status"] == "done":
            yield task          # yield = lazy return (like C# yield return)

for task in get_done(tasks):
    print(task["status"])
