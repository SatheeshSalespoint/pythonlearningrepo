# Day 1 Exercise — Filter Tasks by Status

tasks = [
    {"title": "Buy groceries", "status": "pending"},
    {"title": "Write report", "status": "done"},
    {"title": "Fix bug", "status": "in-progress"},
    {"title": "Send email", "status": "pending"},
]

# used for loop with if
def filter_tasks(tasks, status):
    result=[];
    for task in tasks:
        if task["status"] == status:
            result.append(task)  
    return result          


# used while loop with if
def filter_tasks_3(tasks, status):
    index =0
    result=[]
    while index < len(tasks):
        if tasks[index]["status"] == status:
            result.append(tasks[index])
        index+=1 
    return result




# Test it
print(filter_tasks(tasks, "pending"))
print(filter_tasks(tasks, "done"))
print(filter_tasks(tasks, "in-progress"))


# -------------------------------------------------------
# BONUS EXERCISES
# -------------------------------------------------------

# Ex 2 (Easy) — Count tasks by status
def count_by_status(tasks, status):    
    return len(filter_tasks(tasks, status))
    # Return the number of tasks with the given status
    

print(count_by_status(tasks, "pending"))   # Expected: 2


# Ex 3 (Easy) — Get task titles only
def get_titles(tasks):
    result =[]
    for task in tasks:
        result.append(task["title"])
    return result
    

print(get_titles(tasks))   # Expected: ['Buy groceries', 'Write report', 'Fix bug', 'Send email']


# Ex 4 (Medium) — Check if a task exists
def task_exists(tasks, title):
    for task in tasks:
        if(task["title"]== title): 
            return True
        
    return False
    # Return True if a task with that title exists, False otherwise
    

print(task_exists(tasks, "Fix bug"))   # Expected: True
print(task_exists(tasks, "Sleep"))     # Expected: False


# Ex 5 (Medium) — Mark a task as done
def mark_done(tasks, title):
    # Find the task by title and change its status to "done"
    for task in tasks:
        if(task["title"] == title):
            task["status"]="done"  

mark_done(tasks, "Buy groceries")
print(tasks[0])   # Expected: {'title': 'Buy groceries', 'status': 'done'}


# Ex 6 (Challenge) — Group tasks by status
def group_by_status(tasks):
    # Return a dict like: {"pending": [...], "done": [...], "in-progress": [...]}
    result = {}
    for task in tasks:
        if task["status"] not in result:
            result[task["status"]]=[];           
        result[task["status"]].append(task["title"])
    return result      

    

print(group_by_status(tasks))
