# =============================================================================
# Day 10 — Pandas Basics
# Goal: Load, explore, filter and clean data using DataFrames
# =============================================================================

import pandas as pd
import numpy as np

print("=" * 60)
print("BLOCK 1 — What is a DataFrame?")
print("=" * 60)

# A DataFrame is like a spreadsheet / database table in Python.
# Rows = records, Columns = fields.
# Think of it like a List<Dictionary> but much more powerful.

# --- Creating a DataFrame manually ---
data = {
    "title":       ["Buy groceries", "Read Python book", "Go for a run", "Fix bug #42", "Write tests"],
    "status":      ["done", "pending", "done", "in-progress", "pending"],
    "priority":    ["low", "high", "medium", "high", "medium"],
    "is_urgent":   [False, True, False, True, False],
    "duration_hr": [0.5, 2.0, 1.0, 3.5, 2.5],
}

df = pd.DataFrame(data)

print("\nFull DataFrame:")
print(df)

print("\nShape (rows, columns):", df.shape)       # Like .Length in C# but both dimensions
print("Column names:", df.columns.tolist())
print("Data types:\n", df.dtypes)

# --- Accessing a single column (Series) ---
print("\nAll titles:")
print(df["title"])

# A single column is called a Series — like a 1D labelled array
print("\nType of one column:", type(df["title"]))

# --- Accessing a single value ---
print("\nFirst title:", df["title"][0])
print("First row (loc):\n", df.loc[0])             # loc = label-based index
print("First row (iloc):\n", df.iloc[0])           # iloc = position-based index


print("\n" + "=" * 60)
print("BLOCK 2 — Reading CSV Files + Exploring Data")
print("=" * 60)

# Save our DataFrame as a CSV first so we can read it back
csv_path = "pandas-practice/tasks.csv"
df.to_csv(csv_path, index=False)
print(f"Saved to: {csv_path}")

# --- Read it back ---
df_csv = pd.read_csv(csv_path)

print("\nhead(3) — first 3 rows:")
print(df_csv.head(3))       # Like SQL: SELECT TOP 3

print("\ntail(2) — last 2 rows:")
print(df_csv.tail(2))

print("\ninfo() — column types + non-null counts:")
df_csv.info()               # Like a schema view — great for spotting missing data

print("\ndescribe() — statistics for numeric columns:")
print(df_csv.describe())    # count, mean, std, min, max etc. (like SQL DESCRIBE)

print("\nValue counts for 'status':")
print(df_csv["status"].value_counts())   # How many of each status — very useful!

print("\nUnique statuses:", df_csv["status"].unique())
print("Number of unique:", df_csv["status"].nunique())


print("\n" + "=" * 60)
print("BLOCK 3 — Filtering, Selecting Columns, Missing Values")
print("=" * 60)

# --- Selecting specific columns ---
subset = df[["title", "status"]]
print("\nSelected columns (title + status):")
print(subset)

# --- Filtering rows (boolean indexing — same idea as NumPy) ---
pending = df[df["status"] == "pending"]
print("\nPending tasks only:")
print(pending)

high_priority = df[df["priority"] == "high"]
print("\nHigh priority tasks:")
print(high_priority)

# --- Multiple conditions (use & and | not 'and'/'or') ---
urgent_pending = df[(df["is_urgent"] == True) & (df["status"] == "pending")]
print("\nUrgent AND pending:")
print(urgent_pending)

done_or_inprogress = df[(df["status"] == "done") | (df["status"] == "in-progress")]
print("\nDone OR in-progress:")
print(done_or_inprogress)

# --- Adding a new column ---
df["duration_min"] = df["duration_hr"] * 60
print("\nWith duration in minutes:")
print(df[["title", "duration_hr", "duration_min"]])

# --- Sorting ---
print("\nSorted by duration (descending):")
print(df[["title", "duration_hr"]].sort_values("duration_hr", ascending=False))

# --- Missing values ---
print("\n" + "-" * 40)
print("Missing Value Handling")
print("-" * 40)

# Create a DataFrame with intentional missing values
df_missing = pd.DataFrame({
    "title":    ["Task A", "Task B", "Task C", "Task D"],
    "status":   ["done", None, "pending", None],        # None = missing
    "score":    [90, np.nan, 85, np.nan],               # np.nan = missing number
})

print("\nDataFrame with missing values:")
print(df_missing)

print("\nNull check (True = missing):")
print(df_missing.isnull())

print("\nCount of missing values per column:")
print(df_missing.isnull().sum())

# Fill missing status with a default
df_missing["status"] = df_missing["status"].fillna("unknown")
print("\nAfter filling missing status with 'unknown':")
print(df_missing)

# Fill missing score with mean
mean_score = df_missing["score"].mean()
df_missing["score"] = df_missing["score"].fillna(mean_score)
print(f"\nAfter filling missing score with mean ({mean_score}):")
print(df_missing)

# Drop rows that still have any NaN (none left in this case)
df_clean = df_missing.dropna()
print(f"\nAfter dropna() — {len(df_clean)} rows remain:")
print(df_clean)

print("\n" + "=" * 60)
print("BLOCK 4 — Useful Aggregations + groupby")
print("=" * 60)

print("\nMean duration by status:")
print(df.groupby("status")["duration_hr"].mean())

print("\nTask count by priority:")
print(df.groupby("priority")["title"].count())

print("\nTotal hours by priority:")
print(df.groupby("priority")["duration_hr"].sum())

print("\nDay 10 Pandas Basics complete!")
print("Now move on to the exercise: day10_pandas_exercise.py")
