# ============================================================
# Day 9 — NumPy DEEPER DIVE
# Topics: 2D arrays, broadcasting, stacking, copying, real AI use cases
# ============================================================

import numpy as np

# ============================================================
# SECTION A: 2D Arrays (Matrices) — Used EVERYWHERE in AI
# ============================================================
# In AI, images are 2D arrays (pixels), data tables are 2D arrays,
# neural network weights are 2D arrays (matrices).
# Think of a 2D array as a table — rows x columns.

print("=" * 50)
print("SECTION A: 2D Arrays (Matrices)")
print("=" * 50)

# Creating a 2D array — like a table with 3 students, 4 subjects
#              Maths  English  Science  History
students = np.array([
    [85,    72,      90,      68],   # Student 0: Alice
    [91,    88,      76,      95],   # Student 1: Bob
    [74,    65,      83,      79],   # Student 2: Carol
])

print(f"Students array:\n{students}")
print(f"Shape: {students.shape}")   # (3, 4) — 3 rows, 4 columns

# Accessing specific values: [row, column]
print(f"\nAlice's Science score (row 0, col 2): {students[0, 2]}")   # 90
print(f"Bob's entire row:                      {students[1]}")        # all Bob's scores
print(f"Everyone's Maths (column 0):           {students[:, 0]}")     # [85, 91, 74]
print(f"Everyone's English (column 1):         {students[:, 1]}")     # [72, 88, 65]

# Slicing a 2D array
print(f"\nFirst 2 students, first 2 subjects:\n{students[:2, :2]}")


# ============================================================
# SECTION B: Aggregations on 2D Arrays (axis matters!)
# ============================================================
print("\n" + "=" * 50)
print("SECTION B: Axis — Row vs Column aggregations")
print("=" * 50)

# axis=0 → collapse DOWN the rows (result = one value per COLUMN)
# axis=1 → collapse ACROSS the columns (result = one value per ROW)

# Think of it like:
#   axis=0 = "for each subject, what's the average across all students?"
#   axis=1 = "for each student, what's their average across all subjects?"

col_averages = np.mean(students, axis=0)   # average per SUBJECT
row_averages = np.mean(students, axis=1)   # average per STUDENT

print(f"Students array:\n{students}")
print(f"\nAverage per subject (axis=0): {col_averages}")
# Maths avg, English avg, Science avg, History avg

print(f"Average per student (axis=1): {row_averages}")
# Alice avg, Bob avg, Carol avg

print(f"\nBest student (highest row average): Student index {np.argmax(row_averages)}")
print(f"Hardest subject (lowest col average): Subject index {np.argmin(col_averages)}")


# ============================================================
# SECTION C: Broadcasting — NumPy's superpower
# ============================================================
print("\n" + "=" * 50)
print("SECTION C: Broadcasting")
print("=" * 50)

# Broadcasting = applying an operation between arrays of DIFFERENT shapes.
# NumPy "stretches" the smaller array to match the bigger one automatically.

# Example 1: Scalar broadcast (you've already seen this)
arr = np.array([1, 2, 3, 4, 5])
print(f"arr + 10:  {arr + 10}")   # 10 is broadcast to every element

# Example 2: Add a different bonus to each student's scores
# Each student gets a bonus: Alice +5, Bob +3, Carol +7
bonus = np.array([5, 3, 7])

# bonus shape is (3,) — students shape is (3, 4)
# We need bonus as a column: reshape to (3, 1)
bonus_col = bonus.reshape(3, 1)

print(f"\nOriginal scores:\n{students}")
print(f"\nBonus per student: {bonus}")
print(f"\nScores after bonus:\n{students + bonus_col}")
# Each student's row gets their bonus added to every subject

# Example 3: Normalise scores (scale between 0 and 1)
# Used in AI/ML before feeding data into models
min_score = students.min()
print(f"min_score :\n{min_score}")
max_score = students.max()
print(f"max_score :\n{max_score}")
normalised = (students - min_score) / (max_score - min_score)
print(f"\nNormalised scores (0 to 1):\n{normalised.round(2)}")


# ============================================================
# SECTION D: Stacking Arrays (combining data)
# ============================================================
print("\n" + "=" * 50)
print("SECTION D: Stacking Arrays")
print("=" * 50)

# np.vstack — stack vertically (add more rows)
# Like adding more students to the table
new_student = np.array([[88, 79, 91, 85]])   # Dave's scores
all_students = np.vstack([students, new_student])
print(f"After adding Dave:\n{all_students}")
print(f"Shape: {all_students.shape}")   # (4, 4)

# np.hstack — stack horizontally (add more columns)
# Like adding another subject column
pe_scores = np.array([[77], [88], [65], [92]])   # PE scores for all 4 students
with_pe = np.hstack([all_students, pe_scores])
print(f"\nAfter adding PE subject:\n{with_pe}")
print(f"Shape: {with_pe.shape}")   # (4, 5)

# np.concatenate — general purpose stacking
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
print(f"\nConcatenate 1D: {np.concatenate([a, b])}")   # [1 2 3 4 5 6]


# ============================================================
# SECTION E: Copying vs Viewing (IMPORTANT — common bug!)
# ============================================================
print("\n" + "=" * 50)
print("SECTION E: Copy vs View (avoid bugs!)")
print("=" * 50)

original = np.array([10, 20, 30, 40, 50])

# ⚠️  WARNING: Slicing gives a VIEW, not a copy!
# Changing the slice ALSO changes the original — unlike C#!
view = original[1:4]
view[0] = 999

print(f"After changing view[0] to 999:")
print(f"view:     {view}")
print(f"original: {original}")   # 999 is in original too! ← GOTCHA

# ✅  FIX: Use .copy() to get an independent copy
original2 = np.array([10, 20, 30, 40, 50])
safe_copy = original2[1:4].copy()
safe_copy[0] = 999

print(f"\nAfter changing safe_copy[0] to 999:")
print(f"safe_copy: {safe_copy}")
print(f"original2: {original2}")   # original unchanged ✅


# ============================================================
# SECTION F: Where — conditional selection (like SQL WHERE)
# ============================================================
print("\n" + "=" * 50)
print("SECTION F: np.where — conditional selection")
print("=" * 50)

scores = np.array([85, 92, 78, 96, 88, 74, 91])

# np.where(condition, value_if_true, value_if_false)
# Like SQL: CASE WHEN score >= 85 THEN 'Pass' ELSE 'Fail' END
# Like C#: scores.Select(s => s >= 85 ? "Pass" : "Fail")

result = np.where(scores >= 85, "Pass", "Fail")
print(f"Scores: {scores}")
print(f"Result: {result}")

# Get INDICES where condition is true (like finding row numbers)
passing_indices = np.where(scores >= 85)[0]
print(f"Passing student indices: {passing_indices}")
print(f"Passing scores:          {scores[passing_indices]}")


# ============================================================
# SECTION G: Real AI Use Case — Dot Product
# ============================================================
print("\n" + "=" * 50)
print("SECTION G: Dot Product (used in neural networks!)")
print("=" * 50)

# In neural networks, every layer does: output = inputs · weights
# The dot product multiplies matching elements and sums them up

# Example: A student has 3 feature scores — study hours, sleep hours, practice tests
student_features = np.array([8, 7, 5])   # 8hrs study, 7hrs sleep, 5 practice tests

# Each feature has a weight (importance) — determined by training
weights = np.array([0.5, 0.3, 0.2])   # study matters most

# Dot product = (8×0.5) + (7×0.3) + (5×0.2) = 4 + 2.1 + 1 = 7.1
prediction = np.dot(student_features, weights)
print(f"Student features: {student_features}")
print(f"Weights:          {weights}")
print(f"Predicted score:  {prediction}")   # 7.1 out of 10

# Matrix dot product — multiple students at once
all_students_features = np.array([
    [8, 7, 5],   # Alice
    [5, 8, 3],   # Bob
    [9, 6, 8],   # Carol
])
all_predictions = np.dot(all_students_features, weights)
print(f"\nAll predictions: {all_predictions}")


# ============================================================
# 🏋️ EXERCISE — Deeper NumPy
# ============================================================
print("\n" + "=" * 50)
print("EXERCISE — Your Turn!")
print("=" * 50)

# You have monthly sales data for 3 salespeople over 4 months:
#              Jan  Feb  Mar  Apr
# Alice:       120, 135, 110, 150
# Bob:         98,  105, 120, 115
# Carol:       145, 130, 155, 160

# TODO 1: Create a 2D NumPy array called `sales`
# TODO 2: Print Alice's total sales (sum of row 0)
# TODO 3: Print the best month overall (highest column average — use axis=0)
# TODO 4: Print each person's average monthly sales (use axis=1)
# TODO 5: Use np.where to label each person as "Target Met" if their average > 125, else "Below Target"
# BONUS:  Normalise the sales data between 0 and 1

# Write your code below:
sales =np.array([[120,135,110,150],
        [98,105,120,115],
        [145,130,155,160]])

print(f"Sales {sales}");
row_sum = np.sum(sales[0])
print(f" Alice total sales {row_sum}")
monthly_mean= np.mean(sales,axis=0)
print(f"Print average monthly sales {monthly_mean}")
print(f"Print the best month overall {np.max(monthly_mean)}")
perperson_mean= np.mean(sales,axis=1)
print(f"Print each person's average monthly sales {perperson_mean}")
print(f"Use np.where to label each person {np.where(perperson_mean > 125,"Target Met","Below Target")}")

min_sale= sales.min()
max_sale= sales.max()
normalize_sale = (sales - min_sale)/(max_sale-min_sale)
print(f"Normalize sale {normalize_sale}")