# =============================================================================
# Day 10 — Pandas Exercise
# Goal: Load a tasks CSV, filter and analyse it using Pandas
# =============================================================================
# Instructions:
#   Work through each TODO below. Run the file after each block.
#   Refer to day10_pandas_basics.py if you get stuck.
# =============================================================================

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# SETUP — Create a richer tasks CSV to work with
# ─────────────────────────────────────────────

data = {
    "id":          [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "title":       [
        "Buy groceries", "Read Python book", "Go for a run",
        "Fix bug #42", "Write tests", "Team meeting",
        "Code review", "Update docs", "Deploy to prod", "Sprint planning"
    ],
    "status":      ["done", "pending", "done", "in-progress", "pending",
                    "done", "in-progress", "pending", "done", "pending"],
    "priority":    ["low", "high", "medium", "high", "medium",
                    "low", "high", "medium", "high", "low"],
    "is_urgent":   [False, True, False, True, False, False, True, False, True, False],
    "duration_hr": [0.5, 2.0, 1.0, 3.5, 2.5, 1.0, 2.0, 1.5, 0.5, 2.0],
    "owner":       ["Alice", "Bob", "Alice", "Charlie", "Bob",
                    "Alice", "Charlie", "Bob", None, "Charlie"],
}

csv_path = "pandas-practice/tasks_exercise.csv"
pd.DataFrame(data).to_csv(csv_path, index=False)
print(f"CSV created at: {csv_path}\n")


# ─────────────────────────────────────────────
# EXERCISE 1 — Load and explore the CSV
# ─────────────────────────────────────────────
print("=" * 50)
print("EXERCISE 1 — Load and Explore")
print("=" * 50)

# TODO 1a: Read the CSV into a DataFrame called `tasks`
tasks = pd.read_csv(csv_path)  # replace with pd.read_csv(...)
print(f"Read CSV {tasks}");

# TODO 1b: Print the first 5 rows
# your code here
print(f"Print the first 5 rows {tasks.head(5)}")

# TODO 1c: Print shape, column names, and data types (use .info())
# your code here
print(f"Print shape, column names, and data types{tasks.info()}")

# TODO 1d: Print summary statistics for numeric columns
# your code here
print(f"Print summary statistics for numeric columns{tasks.describe()}")

# ─────────────────────────────────────────────
# EXERCISE 2 — Filter tasks
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 2 — Filter Tasks")
print("=" * 50)

# TODO 2a: Print all tasks where status == "pending"
# your code here
print(f"Print all tasks where status is pending {tasks[tasks["status"]=="pending"]}")

# TODO 2b: Print all tasks where priority == "high" AND is_urgent == True
# your code here
print(f"Print all tasks where priority == `high` {tasks[tasks["priority"]=="high"]}")

# TODO 2c: Print only the title and status columns for done tasks
# your code here
subtasks= tasks[tasks["status"]=="done"]
print(f"Print only the title and status columns for done tasks {subtasks[["title","status"]]}")

# TODO 2d: Print tasks owned by "Alice", sorted by duration_hr descending
# your code here
tasks_owned_byalice= tasks[tasks["owner"]=="Alice"]
print(f"tasks_owned_byalice{tasks_owned_byalice.sort_values("duration_hr",ascending=False)}")


# ─────────────────────────────────────────────
# EXERCISE 3 — Missing values
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 3 — Missing Values")
print("=" * 50)

# TODO 3a: Print how many missing values are in each column
# your code here
print(f"missing values {tasks.isnull().sum()}")

# TODO 3b: Fill the missing 'owner' with "Unassigned"
# your code here
tasks["owner"]= tasks["owner"].fillna("Unassigned")
print(f"Fill the missing 'owner' with `Unassigned` {tasks}")

# TODO 3c: Confirm there are no more nulls
# your code here
print(f"Confirm there are no more nulls {tasks.dropna()}")

# ─────────────────────────────────────────────
# EXERCISE 4 — Aggregations
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 4 — Aggregations")
print("=" * 50)

# TODO 4a: Print the count of tasks per status (value_counts)
# your code here
print(f"Print the count of tasks per status {tasks["status"].value_counts()}")

# TODO 4b: Print the most common status (the mode — hint: value_counts().idxmax())
# your code here
print(f"Print the most common status {tasks["status"].value_counts().idxmax()}")

# TODO 4c: Print total duration_hr per owner (groupby)
# your code here
print(f"Print total duration_hr per owner (groupby) {tasks.groupby("owner").sum()}")

# TODO 4d: Print average duration_hr per priority
# your code here
print(f"Print average duration_hr per priority {tasks.groupby("priority")["duration_hr"].mean()}")


# ─────────────────────────────────────────────
# EXERCISE 5 — Bonus challenges
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 5 — Bonus")
print("=" * 50)

# TODO 5a: Add a new column 'duration_min' = duration_hr * 60
# your code here
tasks["duration_min"]= tasks["duration_hr"]*60
print(f" Add a new column {tasks}")

# TODO 5b: Add a column 'overdue' — True if status == "pending" and is_urgent == True
# Hint: use a condition like: tasks["overdue"] = (tasks["status"] == ...) & (...)
# your code here
tasks["overdue"] = (tasks["status"] == "pending") & (tasks["is_urgent"] == True)
print(f" Add a column 'overdue' {tasks["overdue"]}")

# TODO 5c: Print how many tasks are overdue
# your code here
print(tasks["overdue"].sum())

# TODO 5d: Save the updated DataFrame (with new columns) to a new CSV called
#          "pandas-practice/tasks_updated.csv"
# your code here
tasks.to_csv("pandas-practice/tasks_updated.csv", index=False)
print("\nExercise complete! Check your output above.")
