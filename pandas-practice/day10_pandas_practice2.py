# =============================================================================
# Day 10 — Pandas Extra Practice
# Same concepts, new data. Try without looking at the basics file!
# Topics: DataFrame, filtering, missing values, aggregations, new columns
# =============================================================================

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────
# SETUP — A student exam results dataset
# ─────────────────────────────────────────────

data = {
    "student":  ["Alice", "Bob", "Charlie", "Diana", "Eve",
                 "Frank", "Grace", "Hank", "Ivy", "Jack"],
    "subject":  ["Math", "Math", "Science", "Math", "Science",
                 "English", "English", "Science", "Math", "English"],
    "score":    [85, 92, 78, None, 95, 60, None, 88, 73, 55],
    "grade":    ["B", "A", "C", None, "A", "D", None, "B", "C", "F"],
    "passed":   [True, True, True, None, True, False, None, True, True, False],
    "attempts": [1, 1, 2, 1, 1, 3, 2, 1, 2, 3],
}

df = pd.DataFrame(data)
csv_path = "pandas-practice/students.csv"
df.to_csv(csv_path, index=False)
print(f"Dataset ready: {csv_path}\n")


# ─────────────────────────────────────────────
# PRACTICE 1 — Load and Explore
# ─────────────────────────────────────────────
print("=" * 50)
print("PRACTICE 1 — Load and Explore")
print("=" * 50)

# 1a. Read the CSV into a variable called `students`
# your code here
students = pd.read_csv(csv_path)
print(f"Students {students}")

# 1b. Print the first 4 rows
# your code here
print(f"Print the first 4 rows {students.head(4)}")

# 1c. Print the shape — how many rows and columns?
# your code here
print(f"Print the shape {students.shape}")

# 1d. Print column names and data types using .info()
# your code here
print(f"Print column names and data types {students.info()}")

# 1e. Print statistics for numeric columns using .describe()
# your code here
print(f"Print statistics {students.describe()}")

# ─────────────────────────────────────────────
# PRACTICE 2 — Selecting and Filtering
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("PRACTICE 2 — Selecting and Filtering")
print("=" * 50)

# 2a. Print only the 'student' and 'score' columns
# your code here
print(f"Print only the 'student' and 'score' columns{students[["student","score"]]}")

# 2b. Print all rows where subject == "Math"
# your code here
print(f"Print all rows where subject == `Math`{students[students["subject"]=="Math"]}")

# 2c. Print all students who passed (passed == True)
# your code here
print(f"Print all students who passed == True {students[students["passed"]== True]}")

# 2d. Print students who scored above 80
# your code here
print(f"Print students who scored above 80{students[students["score"] > 80]}")

# 2e. Print students who FAILED (passed == False) AND took more than 1 attempt
# your code here
print(f"Print students who FAILED (passed == False) AND took more than 1 attempt {students[(students["passed"]== False) & (students["attempts"] > 1)]}")

# 2f. Print students who study "Science" OR "English"
# your code here
print(f" Print students who study 'Science' OR 'English' {students[(students["subject"]== "Science") | (students["subject"] == "English")]}")

# 2g. Print just student names and scores for Math students, sorted by score descending
# your code here
mathstudents= students[students["subject"] == "Math"]
studentsnamesandscores = mathstudents[["student","score"]]
print(f" Print just student names and scores for Math students, sorted by score descending {studentsnamesandscores.sort_values("score", ascending=False)}")


# ─────────────────────────────────────────────
# PRACTICE 3 — Missing Values
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("PRACTICE 3 — Missing Values")
print("=" * 50)

# 3a. How many missing values are in each column?
# your code here
print(f"{students.isnull().sum()}")

# 3b. Fill missing 'score' with the mean score
# your code here
mean = students["score"].mean()
students["score"]= students["score"].fillna(mean)
print(f"{students["score"]}")

# 3c. Fill missing 'grade' with "Pending"
# your code here
students["grade"]= students["grade"].fillna("Pending")
print(f"{students["grade"]}")

# 3d. Fill missing 'passed' with False
# your code here
students["passed"]= students["passed"].fillna(False)
print(f"{students["passed"]}")
# 3e. Confirm there are no more nulls (print isnull().sum())
# your code here
print(f"{students.isnull().sum()}")

# ─────────────────────────────────────────────
# PRACTICE 4 — Aggregations
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("PRACTICE 4 — Aggregations")
print("=" * 50)

# 4a. How many students are in each subject? (value_counts on 'subject')
# your code here
students["subject"].value_counts()

# 4b. What is the most common subject?  (idxmax)
# your code here
students["subject"].value_counts().idxmax()

# 4c. Average score per subject (groupby)
# your code here
students.groupby("subject")["score"].mean()

# 4d. Total attempts per subject (groupby)
# your code here
students.groupby("subject")["attempts"].sum()

# 4e. Highest score per subject (groupby + max)
# your code here
students.groupby("subject")["score"].max()

# ─────────────────────────────────────────────
# PRACTICE 5 — New Columns + Save
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("PRACTICE 5 — New Columns and Save")
print("=" * 50)

# 5a. Add a column 'score_out_of_10' = score / 10  (rounded to 1 decimal)
# Hint: round(students["score"] / 10, 1)
# your code here
students["score_out_of_10"] = round(students["score"] / 10, 1)
# 5b. Add a column 'needs_retry' = True if passed == False AND attempts < 3
# your code here
students["needs_retry"] = (students["passed"] ==False) & (students["attempts"] < 3)

# 5c. Print how many students need a retry
# your code here
students["needs_retry"].sum()

# 5d. Save the final DataFrame to "pandas-practice/students_updated.csv"
# your code here

students.to_csv("pandas-practice/students_updated.csv",index=False)

print("\nPractice complete!")
