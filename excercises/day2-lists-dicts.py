# -------------------------------------------------------
# Day 2 — Lists & Dictionaries Exercises
# -------------------------------------------------------

tasks = [
    {"title": "Buy groceries", "status": "pending", "priority": 2},
    {"title": "Fix bug", "status": "in-progress", "priority": 1},
    {"title": "Write report", "status": "done", "priority": 3},
    {"title": "Send email", "status": "pending", "priority": 1},
    {"title": "Deploy app", "status": "in-progress", "priority": 2},
]


# -------------------------------------------------------
# LIST EXERCISES
# -------------------------------------------------------

# Ex 1 (Easy) — Get the first and last task title
# Expected: "Buy groceries" and "Deploy app"
def first_and_last(tasks):
    return [tasks[0]["title"],tasks[-1]["title"]]

print(first_and_last(tasks))


# Ex 2 (Easy) — Add a new task to the list
# Add {"title": "Review PR", "status": "pending", "priority": 1}
# Expected: 6 tasks total
def add_task(tasks, new_task):
    tasks.append(new_task)

add_task(tasks, {"title": "Review PR", "status": "pending", "priority": 1})
print(len(tasks))  # Expected: 6


# Ex 3 (Easy) — Remove a task by title
# Remove the task with title "Write report"
# Expected: 5 tasks remain
def remove_task(tasks, title):
    for task in tasks:
        if task["title"] == title:
            tasks.remove(task)

remove_task(tasks, "Write report")
print(len(tasks))  # Expected: 5


# Ex 4 (Medium) — Sort tasks by priority (lowest number = highest priority)
# Expected: tasks ordered by priority field ascending
def sort_by_priority(tasks):
    return sorted(tasks, key=lambda t: t["priority"]) # i have referred. give me best solution       

sorted_tasks = sort_by_priority(tasks)
for t in sorted_tasks:
    print(t["priority"], t["title"])


# Ex 5 (Medium) — Get titles of all pending tasks as a list
# Expected: ['Buy groceries', 'Send email']
def pending_titles(tasks):
    result=[]
    for task in tasks:
        if(task["status"] == "pending"):
            result.append(task["title"])
    return result

print(pending_titles(tasks))


# -------------------------------------------------------
# DICTIONARY EXERCISES
# -------------------------------------------------------

# Ex 6 (Easy) — Get all keys and values of the first task
# Expected: print each key and value on a separate line
def print_task_details(task):
    for key, value in task.items():
        print(f"{key}: {value}")   


print_task_details(tasks[0])


# Ex 7 (Medium) — Merge two task dicts
# Combine task info with extra metadata, result should have all fields
# Expected: {"title": "Fix bug", "status": "in-progress", "priority": 1, "assigned_to": "Satheesh", "due": "2026-06-15"}
task_info = {"title": "Fix bug", "status": "in-progress", "priority": 1}
task_meta = {"assigned_to": "Satheesh", "due": "2026-06-15"}

def merge_task(task_info, task_meta):
    for key in task_meta:
        task_info[key] = task_meta[key]

    return task_info

print(merge_task(task_info, task_meta))


# Ex 8 (Medium) — Count tasks per priority level
# Expected: {1: 2, 2: 2, 3: 1}  (before removals above)
def count_by_priority(tasks):
    result={}
    for task in tasks:
        if task["priority"] not in result:
            result[task["priority"]]=0
        result[task["priority"]]+=1

    return result
    
        

print(count_by_priority(tasks))


# Ex 9 (Challenge) — Find the highest priority pending task
# Return the pending task with the lowest priority number
# Expected: {"title": "Send email", "status": "pending", "priority": 1}
def top_pending_task(tasks):
    
    pending = [ t for task in tasks if task["status"]== "pending"] 
    return min (pending, key=lambda t: t["priority"])         

print(top_pending_task(tasks))
