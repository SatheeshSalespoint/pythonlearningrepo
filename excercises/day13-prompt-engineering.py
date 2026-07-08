import ollama
import json
import re

MODEL = "qwen2.5-coder:7b"

def parse_json(text: str) -> dict:
    """Safely parse JSON from LLM output — strips markdown code blocks if present."""
    # Remove ```json ... ``` or ``` ... ``` wrappers
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
    return json.loads(cleaned)

# def ask(prompt: str) -> str:
#     response = ollama.chat(
#         model=MODEL,
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return response.message.content

# def assignrole(messages: []) -> str: # type: ignore
#     response = ollama.chat(
#         model=MODEL,
#         messages=messages
#     )
#     return response.message.content

# def build_priority_prompt(task_title: str, task_description: str, context: str) -> str:
#     """
#     Dynamic prompt template combining Role + Few-shot + CoT + Dynamic data.
#     Role      → 'You are a senior project manager...'
#     Few-shot  → 3 examples showing High/Medium/Low
#     CoT       → 'Think step by step...'
#     Dynamic   → task_title, task_description, context injected at runtime
#     """
#     return f"""
# You are a senior software project manager with 10 years experience.
# Your job is to prioritise development tasks based on business impact.
# Always respond ONLY in JSON format: {{"priority": "...", "reason": "..."}}

# Examples:
# Task: "Fix login bug"  | Description: "All users locked out"     → {{"priority": "High",   "reason": "Blocks all users from accessing the system"}}
# Task: "Add dark mode"  | Description: "UI preference feature"    → {{"priority": "Low",    "reason": "Nice to have, no users are blocked"}}
# Task: "Slow dashboard" | Description: "Takes 10 seconds to load" → {{"priority": "Medium", "reason": "Degrades experience but system still works"}}

# Now analyse this task step by step, then give your answer.
# Think about: who is affected? is anyone blocked? is it a production issue?

# Task Title: {task_title}
# Description: {task_description}
# Context: {context}
# """


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

# messages = [
#     {
#         "role": "system",
#         "content": """You are a software project manager assistant.
# Your job is to help prioritise development tasks.
# Rules:
# - Always respond in JSON format
# - Priority must be: High, Medium, or Low
# - Always explain your reasoning in 1 sentence
# """
#     },
#     {
#         "role": "user",
#         "content": "Should I fix the login bug or add the dark mode feature first?"
#     }
# ]

# print(assignrole(messages))

# ---- PART 5: Dynamic Template (Role + Few-shot + CoT combined) ----
# print("=== DYNAMIC TEMPLATE (Role + Few-shot + CoT) ===")

# system_role = "You are a senior software project manager. Always respond in JSON."

# tasks = [
#     {
#         "title": "Password reset not working",
#         "description": "Users click reset link but get a 500 error",
#         "context": "Reported by 3 customers this morning, production issue"
#     },
#     {
#         "title": "Add export to CSV feature",
#         "description": "Users want to download their task list as a CSV file",
#         "context": "Requested by 2 users in feedback form last month"
#     }
# ]

# for task in tasks:
#     prompt = build_priority_prompt(task["title"], task["description"], task["context"])
#     result = assignrole([
#         {"role": "system", "content": system_role},
#         {"role": "user",   "content": prompt}
#     ])
#     print(f"\nTask: {task['title']}")
#     print(result)

    # ---- PART 6: Negative Prompting ----
# print("\n=== WITHOUT NEGATIVE PROMPTING ===")
# without_negative = "Classify this task priority: 'Fix login bug'"
# print(ask(without_negative))

# print("\n=== WITH NEGATIVE PROMPTING ===")
# with_negative = """
# Classify this task priority: 'Fix login bug'

# Rules:
# - Respond ONLY with JSON: {"priority": "..."}
# - Do NOT explain your answer
# - Do NOT add any text before or after the JSON
# - Do NOT add disclaimers
# """
# print(ask(with_negative))

# # ---- PART 7: Contextual Prompting ----
# print("\n=== CONTEXTUAL PROMPTING ===")

# tasks = [
#     {"id": 1, "title": "Fix login bug",       "status": "pending"},
#     {"id": 2, "title": "Add dark mode",        "status": "pending"},
#     {"id": 3, "title": "DB migration failing", "status": "pending"},
#     {"id": 4, "title": "Update footer text",   "status": "pending"},
# ]

# context = "\n".join([f"- [{t['id']}] {t['title']}" for t in tasks])

# prompt = f"""
# You are a software project manager.
# Here are the current pending tasks:

# {context}

# Which ONE task should be done first and why?
# Do NOT explain at length.
# Respond ONLY in JSON: {{"task_id": 1, "reason": "one sentence"}}
# """

# result = ask(prompt)
# print(result)

# # Parse and use it like real code would
# data = parse_json(result)
# chosen = next(t for t in tasks if t["id"] == data["task_id"])
# print(f"\nAI recommends: [{chosen['id']}] {chosen['title']}")
# print(f"Reason: {data['reason']}")



# Excercise
print("\n=== Excercise PROMPTING ===")
tasks = [
    {"id": 1, "title": "Fix login bug",         "status": "pending", "days_pending": 3},
    {"id": 2, "title": "Add dark mode",          "status": "pending", "days_pending": 1},
    {"id": 3, "title": "DB migration failing",   "status": "pending", "days_pending": 0},
    {"id": 4, "title": "Update footer text",     "status": "pending", "days_pending": 7},
]
developer_name = "Satheesh"

def build_task_advice(tasks, developer_name):
    return '\n'.join([f"- Task {task['id']}: {task['title']} | days pending: {task['days_pending']}" for task in tasks])

def assignrole():
    prompt = build_task_advice(tasks, developer_name)
    return  [
        {"role": "system","content": """You are an Senior software engineer. 
         classify this task with these details ( recommended task id, priority order, reason, warning), 
         Return the result in Json format"""
         },
        {"role": "user", "content": f"""        
                

      Example 1:
Tasks: Login bug (3 days), Dark mode (1 day), DB down (0 days)
Decision: {{"recommended_task_id": 3, "reason": "DB down blocks everyone"}}

Example 2:
Tasks: CSS fix (5 days), Payment failing (1 day)  
Decision: {{"recommended_task_id": 2, "reason": "Payment failure loses revenue"}}

         Here is the task list {prompt}

         Think step by step:
1. Which task blocks the most users?
2. Which has been pending longest?
3. Which is a production issue?
Then give your recommendation.

        DONT provide assumptions
        DONT return reply as plain text
        DONT add markdown code blocks
        Respond ONLY in this exact JSON format:
        {{"recommended_task_id": 3, "priority_order": [3, 1, 4, 2], "reason": "one sentence", "warning": "one sentence"}}

        """
        }
    ]
messages= assignrole()


response = ollama.chat(model = MODEL, messages=messages )


data = parse_json(response.message.content)

print(f"{data}")





