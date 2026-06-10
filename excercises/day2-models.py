# -------------------------------------------------------
# day2-models.py — Your own module (like a C# class library)
# This file will be imported by day2-modules.py
# -------------------------------------------------------

# Ex 1 — Task class (to be imported)
class Task:
    def __init__(self, title, status):
        self.title = title
        self.status = status

    def display(self):
        print(f"[{self.status}] {self.title}")

    def mark_done(self):
        self.status = "done"

    def is_pending(self):
        return self.status == "pending"

    def __str__(self):
        return f"[{self.status}] {self.title}"


# Ex 2 — TaskList class (to be imported)
class TaskList:
    def __init__(self):
        self.tasks = []

    def add(self, task):
        self.tasks.append(task)

    def show_all(self):
        for task in self.tasks:
            task.display()

    def filter_by_status(self, status):
        return [t for t in self.tasks if t.status == status]

    def count(self):
        return len(self.tasks)


# Ex 3 — Utility functions (to be imported)
def filter_tasks(tasks, status):
    return [t for t in tasks if t["status"] == status]

def get_titles(tasks):
    return [t["title"] for t in tasks]
