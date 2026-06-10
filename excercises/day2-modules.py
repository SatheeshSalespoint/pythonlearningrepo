# -------------------------------------------------------
# Day 2 — Modules & Imports Exercises
# -------------------------------------------------------
# Run this file from the excercises folder:
#   cd excercises
#   python day2-modules.py
# -------------------------------------------------------


# -------------------------------------------------------
# Ex 1 (Easy) — Import built-in modules
# -------------------------------------------------------
# Use the math module to:
#   - Print square root of 144
#   - Print value of pi (rounded to 2 decimal places)
# Use the random module to:
#   - Print a random task from the list below

import math
import random

tasks = ["Fix bug", "Write report", "Deploy app", "Send email", "Review PR"]

# Your code here
# Expected:
# sqrt(144) = 12.0
# pi = 3.14
# Random task: <one of the tasks above>
t = math.sqrt(144)
pi= math.pi
print(f"Random task :{random.choice(tasks)}")

# -------------------------------------------------------
# Ex 2 (Easy) — Import from datetime
# -------------------------------------------------------
# Print today's date in format: "Today is 2026-06-10"
# Hint: use datetime.now().strftime("%Y-%m-%d")

from datetime import datetime

# Your code here
# Expected: Today is 2026-06-10
print(f"Today is {datetime.now().strftime("%Y-%m-%d")}")

# -------------------------------------------------------
# Ex 3 (Medium) — Import your own module
# -------------------------------------------------------
# Import Task and TaskList from day2-models.py
# Create 3 tasks, add to TaskList, show all

from day2_models import Task, TaskList

t = Task("Buy groceries","pending")
t.display()
t1 = Task("Fix bug","in-progress")
t1.display()
t2 = Task("Write report","pending")
t2.mark_done()
t2.display()

ts= TaskList()
ts.add(Task("Buy groceries","pending"))
ts.add(Task("Fix bug","in-progress"))
ts.add(Task("Write report","done"))
ts.show_all()

# Your code here
# Expected:
# [pending] Buy groceries
# [in-progress] Fix bug
# [done] Write report


# -------------------------------------------------------
# Ex 4 (Medium) — Import specific function from your module
# -------------------------------------------------------
# Import only filter_tasks and get_titles from day2-models.py
# Use them on the dict-based tasks list below

from day2_models import filter_tasks, get_titles

dict_tasks = [
    {"title": "Buy groceries", "status": "pending"},
    {"title": "Write report", "status": "done"},
    {"title": "Fix bug", "status": "in-progress"},
    {"title": "Send email", "status": "pending"},
]

print(f"Pending Tasks:{filter_tasks(dict_tasks, 'pending')}")
print(f"All Titles:{get_titles(dict_tasks)}")

# Your code here
# Expected:
# Pending tasks: [{'title': 'Buy groceries', ...}, {'title': 'Send email', ...}]
# All titles: ['Buy groceries', 'Write report', 'Fix bug', 'Send email']


# -------------------------------------------------------
# Ex 5 (Challenge) — Use datetime to timestamp tasks
# -------------------------------------------------------
# Update the Task class usage below to record created_at time
# Print each task like: [pending] Fix bug — created at 2026-06-10 10:30:00

from day2_models import Task
from datetime import datetime

class TimestampedTask(Task):
    def __init__(self, title, status):
        # Your code here — call super().__init__() and set self.created_at
        super().__init__(title,status)    
        self.created_at= datetime.now().strftime("%Y-%m-%d %H:%M:%S")    

    def display(self):
        # Print like: [pending] Fix bug — created at 2026-06-10 10:30:00
      print(f"[{self.status}] {self.title} -- {self.created_at}")
      

# Test it
t1 = TimestampedTask("Fix bug", "pending")
t2 = TimestampedTask("Deploy app", "in-progress")
t1.display()
t2.display()
