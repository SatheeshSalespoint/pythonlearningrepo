# -------------------------------------------------------
# Day 2 — Classes & OOP Exercises
# -------------------------------------------------------


# -------------------------------------------------------
# Ex 1 (Easy) — Basic Task class
# -------------------------------------------------------
# Create a Task class with:
#   - __init__(self, title, status)
#   - display() method that prints: [pending] Buy groceries

class Task:
    def __init__(self, title, status):
        self.title= title
        self.status= status

    def display(self):
        # Print like: [pending] Buy groceries
        print(f"[{self.status}] {self.title}")

# Test it
t1 = Task("Buy groceries", "pending")
t2 = Task("Fix bug", "in-progress")
t3 = Task("Write report", "done")

t1.display()   # [pending] Buy groceries
t2.display()   # [in-progress] Fix bug
t3.display()   # [done] Write report


# -------------------------------------------------------
# Ex 2 (Easy) — Add __str__ method (like C# ToString())
# -------------------------------------------------------
# Add __str__ to Task so print(task) works directly

class Task2:
    def __init__(self, title, status):
        self.title = title
        self.status = status

    def __str__(self):
        # Return string like: [pending] Buy groceries
        return (f"[{self.status}] {self.title}")
        

# Test it
t = Task2("Send email", "pending")
print(t)   # Expected: [pending] Send email


# -------------------------------------------------------
# Ex 3 (Easy) — Add methods to Task
# -------------------------------------------------------
# Add these methods to the class:
#   - mark_done()     → changes status to "done"
#   - is_pending()    → returns True if status is "pending"

class Task3:
    def __init__(self, title, status):
        self.title = title
        self.status = status

    def display(self):
        print(f"[{self.status}] {self.title}")

    def mark_done(self):
        self.status= "done"

    def is_pending(self):
        return self.status == "pending"

# Test it
t = Task3("Fix bug", "pending")
print(t.is_pending())   # True
t.mark_done()
t.display()             # [done] Fix bug
print(t.is_pending())   # False


# -------------------------------------------------------
# Ex 4 (Medium) — Class variable (like C# static)
# -------------------------------------------------------
# Add a class-level variable task_count
# that increments every time a new Task is created

class Task4:
    task_count = 0   # class variable

    def __init__(self, title, status):
        self.title = title
        self.status= status
        Task4.task_count +=1

# Test it
t1 = Task4("Buy groceries", "pending")
t2 = Task4("Fix bug", "in-progress")
t3 = Task4("Write report", "done")
print(Task4.task_count)   # Expected: 3


# -------------------------------------------------------
# Ex 5 (Medium) — TaskList class
# -------------------------------------------------------
# Create a TaskList class that:
#   - stores a list of Task objects
#   - add(task)                  → adds a task
#   - show_all()                 → calls display() on each task
#   - filter_by_status(status)   → returns list of tasks matching status
#   - count()                    → returns total number of tasks

class TaskList:
    def __init__(self):
        pass     

    def add(self, task):
        # Your code here
        pass

    def show_all(self):
        # Your code here
        pass

    def filter_by_status(self, status):
        # Return list of Task objects matching the status
        pass

    def count(self):
        # Return total number of tasks
        pass

# Test it
tl = TaskList()
tl.add(Task("Buy groceries", "pending"))
tl.add(Task("Fix bug", "in-progress"))
tl.add(Task("Write report", "done"))
tl.add(Task("Send email", "pending"))

tl.show_all()
print(tl.count())                          # Expected: 4
pending = tl.filter_by_status("pending")
for t in pending:
    t.display()                            # Expected: 2 pending tasks


# -------------------------------------------------------
# Ex 6 (Challenge) — Inheritance: UrgentTask
# -------------------------------------------------------
# Create UrgentTask that inherits from Task:
#   - adds priority field (e.g. "high", "medium")
#   - overrides display() → [pending][HIGH] Fix bug
#   - inherits mark_done() and is_pending() from Task (no re-write needed)

class UrgentTask(Task):
    def __init__(self, title, status, priority):
        # Your code here — use super().__init__()
        super().__init__(title, status)
        self.priority= priority

        

    def display(self):
        # Print like: [pending][HIGH] Fix bug
        print(f"[{self.status}][{self.priority}] {self.title}")
        

# Test it
ut = UrgentTask("Fix bug", "pending", "high")
ut.display()              # [pending][HIGH] Fix bug
ut.mark_done()            # inherited from Task
ut.display()              # [done][HIGH] Fix bug
print(ut.is_pending())    # False — inherited from Task
