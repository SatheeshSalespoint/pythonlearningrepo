# -------------------------------------------------------
# Day 2 Exercise — Task Class (OOP)
# -------------------------------------------------------


# -------------------------------------------------------
# MAIN EXERCISE — Task class with title, status, display
# -------------------------------------------------------

class Task:
    def __init__(self, title, status):
        # Your code here
        pass

    def display(self):
        # Print like: [pending] Buy groceries
        pass

# Test it
t1 = Task("Buy groceries", "pending")
t2 = Task("Fix bug", "in-progress")
t3 = Task("Write report", "done")

t1.display()
t2.display()
t3.display()


# -------------------------------------------------------
# BONUS 1 — Add a mark_done() method
# -------------------------------------------------------
# Add a method that changes the status to "done"
# then call display() again to verify

# Expected:
# t1.mark_done()
# t1.display()  →  [done] Buy groceries


# -------------------------------------------------------
# BONUS 2 — Add a TaskList class
# -------------------------------------------------------
# Create a TaskList class that:
# - holds a list of Task objects
# - has add(task) method to add a task
# - has show_all() method to display all tasks
# - has filter_by_status(status) method that returns matching tasks

class TaskList:
    def __init__(self):
        # Your code here
        pass

    def add(self, task):
        # Your code here
        pass

    def show_all(self):
        # Your code here
        pass

    def filter_by_status(self, status):
        # Return list of tasks matching the given status
        pass

# Test it
# tl = TaskList()
# tl.add(Task("Buy groceries", "pending"))
# tl.add(Task("Fix bug", "in-progress"))
# tl.add(Task("Write report", "done"))
# tl.show_all()
# print(tl.filter_by_status("pending"))


# -------------------------------------------------------
# BONUS 3 — Inheritance
# -------------------------------------------------------
# Create an UrgentTask class that inherits from Task
# - adds a priority field (e.g. "high")
# - overrides display() to show: [pending][HIGH] Buy groceries

class UrgentTask(Task):
    def __init__(self, title, status, priority):
        # Your code here (hint: use super().__init__())
        pass

    def display(self):
        # Your code here
        pass

# Test it
# ut = UrgentTask("Buy groceries", "pending", "high")
# ut.display()  →  [pending][HIGH] Buy groceries
