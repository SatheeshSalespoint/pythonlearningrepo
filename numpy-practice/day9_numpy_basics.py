# ============================================================
# Day 9 — NumPy Basics
# Run each section one at a time. Read the output carefully.
# ============================================================

import numpy as np

# ============================================================
# SECTION 1: What is NumPy? Why not just use Python lists?
# ============================================================
print("=" * 50)
print("SECTION 1: Lists vs NumPy Arrays")
print("=" * 50)

# Python list
python_list = [10, 20, 30, 40, 50]

# NumPy array
numpy_array = np.array([10, 20, 30, 40, 50])

print(f"Python list:   {python_list}")
print(f"NumPy array:   {numpy_array}")

# --- Key difference: math operations ---

# With a Python list, you CAN'T do math directly like this:
# python_list * 2  →  duplicates the list! [10, 20, 30, 10, 20, 30]
# python_list + 5  →  ERROR

# With NumPy, math works element-by-element (like C# LINQ .Select(x => x * 2)):
print(f"\nList * 2 (Python):   {python_list * 2}")   # duplicates!
print(f"Array * 2 (NumPy):   {numpy_array * 2}")    # multiplies each!
print(f"Array + 5 (NumPy):   {numpy_array + 5}")    # adds 5 to each!

# --- Why AI/ML needs this ---
# In AI, you work with thousands of numbers (pixel values, weights, scores).
# NumPy operates on ALL of them at once — much faster than a Python for-loop.

print(f"\nType of list:  {type(python_list)}")
print(f"Type of array: {type(numpy_array)}")
print(f"Array dtype:   {numpy_array.dtype}")   # int64 — all elements same type


# ============================================================
# SECTION 2: Creating Arrays
# ============================================================
print("\n" + "=" * 50)
print("SECTION 2: Creating Arrays")
print("=" * 50)

# 2a. From a Python list
scores = np.array([85, 92, 78, 96, 88])
print(f"From list:      {scores}")

# 2b. np.zeros() — all zeros (like initialising a C# array with default values)
zeros = np.zeros(5)
print(f"np.zeros(5):    {zeros}")

zeros_2d = np.zeros((3, 4))  # 3 rows, 4 columns (2D array / matrix)
print(f"np.zeros(3x4):\n{zeros_2d}")

# 2c. np.ones() — all ones
ones = np.ones(5)
print(f"np.ones(5):     {ones}")

# 2d. np.arange() — like Python range(), but returns an array
# np.arange(start, stop, step)  →  stop is EXCLUSIVE
range_arr = np.arange(0, 10, 2)
print(f"np.arange(0,10,2): {range_arr}")   # [0, 2, 4, 6, 8]

# 2e. np.linspace() — evenly spaced numbers between two values
# Useful in AI for generating test data / graph points
linspace_arr = np.linspace(0, 1, 5)   # 5 points between 0 and 1
print(f"np.linspace(0,1,5): {linspace_arr}")

# 2f. Random arrays (very common in AI for weight initialisation)
np.random.seed(42)  # seed = reproducible results (same "random" every time)
random_arr = np.random.rand(5)   # 5 random floats between 0 and 1
print(f"Random array:   {random_arr}")


# ============================================================
# SECTION 3: Array Shape, Size, and Dimensions
# ============================================================
print("\n" + "=" * 50)
print("SECTION 3: Shape, Size, Dimensions")
print("=" * 50)

a = np.array([1, 2, 3, 4, 5, 6])

print(f"Array:    {a}")
print(f"Shape:    {a.shape}")   # (6,) — 1D, 6 elements
print(f"Size:     {a.size}")    # 6 total elements
print(f"Ndim:     {a.ndim}")    # 1 dimension

# Reshape: change shape without changing data
# Think of it like: same 6 numbers, arranged differently
b = a.reshape(2, 3)   # 2 rows, 3 columns
print(f"\nReshaped (2x3):\n{b}")
print(f"Shape:    {b.shape}")   # (2, 3)
print(f"Ndim:     {b.ndim}")    # 2 dimensions

# 2D array (matrix) — rows x columns
matrix = np.array([
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
])
print(f"\nMatrix:\n{matrix}")
print(f"Shape:    {matrix.shape}")  # (3, 3)


# ============================================================
# SECTION 4: Indexing and Slicing
# ============================================================
print("\n" + "=" * 50)
print("SECTION 4: Indexing and Slicing")
print("=" * 50)

arr = np.array([10, 20, 30, 40, 50])

# Single element (0-indexed, like C#)
print(f"arr[0]:    {arr[0]}")    # 10
print(f"arr[-1]:   {arr[-1]}")   # 50  (last element — Python shortcut)

# Slicing: arr[start:stop]  →  stop is EXCLUSIVE (like C# range)
print(f"arr[1:3]:  {arr[1:3]}")  # [20, 30]
print(f"arr[:3]:   {arr[:3]}")   # [10, 20, 30]  (from beginning)
print(f"arr[2:]:   {arr[2:]}")   # [30, 40, 50]  (to end)

# 2D array indexing: [row, column]
matrix = np.array([
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
])
print(f"\nmatrix[0, 1]:  {matrix[0, 1]}")   # row 0, col 1 → 2
print(f"matrix[1]:     {matrix[1]}")         # entire row 1 → [4, 5, 6]
print(f"matrix[:, 0]:  {matrix[:, 0]}")     # all rows, col 0 → [1, 4, 7]

# Boolean indexing — filter by condition (like C# .Where())
scores = np.array([85, 92, 78, 96, 88])
high_scores = scores[scores > 88]
print(f"\nScores:         {scores}")
print(f"Scores > 88:    {high_scores}")   # [92, 96]


# ============================================================
# SECTION 5: Math Operations
# ============================================================
print("\n" + "=" * 50)
print("SECTION 5: Math Operations")
print("=" * 50)

a = np.array([1, 2, 3, 4])
b = np.array([10, 20, 30, 40])

# Element-wise operations (applies to each pair)
print(f"a + b:   {a + b}")     # [11, 22, 33, 44]
print(f"a * b:   {a * b}")     # [10, 40, 90, 160]
print(f"b / a:   {b / a}")     # [10, 10, 10, 10]
print(f"a ** 2:  {a ** 2}")    # [1, 4, 9, 16]  (squared)

# Math functions
print(f"\nnp.sqrt(a):   {np.sqrt(a)}")        # square root of each
print(f"np.abs([-3, 1, -5]): {np.abs([-3, 1, -5])}")  # absolute value


# ============================================================
# SECTION 6: Aggregations (Summary Statistics)
# ============================================================
print("\n" + "=" * 50)
print("SECTION 6: Aggregations")
print("=" * 50)

scores = np.array([85, 92, 78, 96, 88, 74, 91])

print(f"Scores:   {scores}")
print(f"Sum:      {np.sum(scores)}")      # total
print(f"Mean:     {np.mean(scores):.2f}") # average (:.2f = 2 decimal places)
print(f"Max:      {np.max(scores)}")      # highest
print(f"Min:      {np.min(scores)}")      # lowest
print(f"Std Dev:  {np.std(scores):.2f}")  # how spread out the scores are

# Index of max/min (useful — tells you WHICH student scored highest)
print(f"\nIndex of max: {np.argmax(scores)}")   # position 3 (score=96)
print(f"Index of min: {np.argmin(scores)}")     # position 5 (score=74)


# ============================================================
# 🏋️ EXERCISE — Try it yourself!
# ============================================================
print("\n" + "=" * 50)
print("EXERCISE — Your Turn!")
print("=" * 50)

# 5 students sat an exam. Their scores are:
# Alice: 72, Bob: 88, Carol: 95, Dave: 61, Eve: 83

# TODO 1: Create a NumPy array called `exam_scores` with these values
# TODO 2: Print the average score (use np.mean)
# TODO 3: Print the highest score (use np.max)
# TODO 4: Print only scores above 80 (use boolean indexing)
# TODO 5: BONUS — find which student index got the highest score (use np.argmax)

# Write your code below:
# print("(Complete the exercise above — then run the file again to see your results!)")
exam_scores = np.array([72, 88, 95, 61, 83])
print(f"Scores {exam_scores}")
print(f"Average {np.mean(exam_scores) :.2f}")
print(f"Highest Score {np.max(exam_scores)}")
print(f"Score > 80 {exam_scores[exam_scores > 80]}")
print(f"Highest score index  {np.argmax(exam_scores)}")