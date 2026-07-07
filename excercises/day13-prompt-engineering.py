import ollama

MODEL = "qwen2.5-coder:7b"

def ask(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.message.content

def assignrole(messages: []) -> str: # type: ignore
    response = ollama.chat(
        model=MODEL,
        messages=messages
    )
    return response.message.content

def build_priority_prompt(task_title: str, task_description: str, context: str) -> str:
    """
    Dynamic prompt template combining Role + Few-shot + CoT + Dynamic data.
    Role      → 'You are a senior project manager...'
    Few-shot  → 3 examples showing High/Medium/Low
    CoT       → 'Think step by step...'
    Dynamic   → task_title, task_description, context injected at runtime
    """
    return f"""
You are a senior software project manager with 10 years experience.
Your job is to prioritise development tasks based on business impact.
Always respond ONLY in JSON format: {{"priority": "...", "reason": "..."}}

Examples:
Task: "Fix login bug"  | Description: "All users locked out"     → {{"priority": "High",   "reason": "Blocks all users from accessing the system"}}
Task: "Add dark mode"  | Description: "UI preference feature"    → {{"priority": "Low",    "reason": "Nice to have, no users are blocked"}}
Task: "Slow dashboard" | Description: "Takes 10 seconds to load" → {{"priority": "Medium", "reason": "Degrades experience but system still works"}}

Now analyse this task step by step, then give your answer.
Think about: who is affected? is anyone blocked? is it a production issue?

Task Title: {task_title}
Description: {task_description}
Context: {context}
"""


# ---- PART 1: Zero-shot ----
# print("=== ZERO-SHOT ===")
# zero_shot_prompt = "Classify this task as High, Medium, or Low priority: 'Fix login bug'"
# print(ask(zero_shot_prompt))

# ---- PART 1: Zero-shot ----
# print("=== FEW-SHOT ===")
# few_shot_prompt = """ 
# Classify the task as high, medium or low

# Examples:
# Task: "Fix login bug" → High
# Task: "Update homepage text" → Low
# Task: "Database migration failing in prod" → High
# Task: "Add dark mode" → Medium

# Now classify this:
# Task: "Users can't reset their password"
# """


# print(ask(few_shot_prompt))

# print("=== COT ===")
# COT_Prompt = """
# I have two tasks:
# - Task A: Fix login bug (affects all users, production issue)
# - Task B: Add analytics dashboard (nice to have, no users affected)

# Think step by step about which to prioritise, then give your recommendation.
# """


# print(ask(COT_Prompt))

messages = [
    {
        "role": "system",
        "content": """You are a software project manager assistant.
Your job is to help prioritise development tasks.
Rules:
- Always respond in JSON format
- Priority must be: High, Medium, or Low
- Always explain your reasoning in 1 sentence
"""
    },
    {
        "role": "user",
        "content": "Should I fix the login bug or add the dark mode feature first?"
    }
]

# print(assignrole(messages))

# ---- PART 5: Dynamic Template (Role + Few-shot + CoT combined) ----
print("=== DYNAMIC TEMPLATE (Role + Few-shot + CoT) ===")

system_role = "You are a senior software project manager. Always respond in JSON."

tasks = [
    {
        "title": "Password reset not working",
        "description": "Users click reset link but get a 500 error",
        "context": "Reported by 3 customers this morning, production issue"
    },
    {
        "title": "Add export to CSV feature",
        "description": "Users want to download their task list as a CSV file",
        "context": "Requested by 2 users in feedback form last month"
    }
]

for task in tasks:
    prompt = build_priority_prompt(task["title"], task["description"], task["context"])
    result = assignrole([
        {"role": "system", "content": system_role},
        {"role": "user",   "content": prompt}
    ])
    print(f"\nTask: {task['title']}")
    print(result)

