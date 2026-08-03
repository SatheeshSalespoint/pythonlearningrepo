"""
Day 14 — Exercise: Task Summariser Chain with LangChain
========================================================
Build a task summariser chain that:
  1. Takes a task title + description
  2. Generates a one-line summary
  3. Suggests a priority (High / Medium / Low)
  4. Generates 2-3 action steps

This is the same logic you'll wire into a real FastAPI endpoint on Day 15!

Run: python day14-exercise.py
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama


# ── Setup ─────────────────────────────────────────────────────────────────────
llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.3)
parser = StrOutputParser()


# ── Chain 1: Summary Chain ────────────────────────────────────────────────────
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a project assistant. Be concise and professional."),
    ("user", (
        "Task title: {title}\n"
        "Description: {description}\n\n"
        "Write a one-sentence summary of this task."
    ))
])
summary_chain = summary_prompt | llm | parser


# ── Chain 2: Priority Chain ───────────────────────────────────────────────────
priority_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a project manager. Reply with ONLY one word: High, Medium, or Low."),
    ("user", (
        "Task title: {title}\n"
        "Description: {description}\n\n"
        "What priority should this task be assigned?"
    ))
])
priority_chain = priority_prompt | llm | parser


# ── Chain 3: Action Steps Chain ───────────────────────────────────────────────
steps_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a technical project manager. Be concise."),
    ("user", (
        "Task title: {title}\n"
        "Description: {description}\n\n"
        "List exactly 3 numbered action steps to complete this task. "
        "Each step should be a single short sentence."
    ))
])
steps_chain = steps_prompt | llm | parser


# ── Helper: Run all 3 chains for a task ──────────────────────────────────────
def analyse_task(title: str, description: str) -> dict:
    """
    Analyse a task using 3 LangChain chains.
    Returns a dict with summary, priority, and action_steps.

    C# analogy: like calling 3 separate service methods, each focused on one concern.
    """
    inputs = {"title": title, "description": description}

    summary = summary_chain.invoke(inputs)
    priority = priority_chain.invoke(inputs)
    steps = steps_chain.invoke(inputs)

    return {
        "title": title,
        "summary": summary.strip(),
        "priority": priority.strip(),
        "action_steps": steps.strip(),
    }


# ── Test Tasks ────────────────────────────────────────────────────────────────
test_tasks = [
    {
        "title": "Fix login timeout bug",
        "description": (
            "Users are being logged out after 5 minutes even when they are actively "
            "using the app. Likely a session expiry misconfiguration in the auth middleware."
        )
    },
    {
        "title": "Add dark mode to dashboard",
        "description": (
            "Users have requested a dark mode option. Need to add a toggle button "
            "and apply CSS variables for all UI components."
        )
    },
    {
        "title": "Write API documentation",
        "description": (
            "Document all 12 REST endpoints with request/response examples, "
            "error codes, and authentication requirements."
        )
    },
]


# ── Run the Exercise ──────────────────────────────────────────────────────────
print("=" * 60)
print("TASK ANALYSER — LangChain Exercise")
print("=" * 60)

for i, task in enumerate(test_tasks, 1):
    print(f"\n--- Task {i}: {task['title']} ---")
    result = analyse_task(task["title"], task["description"])

    print(f"Summary  : {result['summary']}")
    print(f"Priority : {result['priority']}")
    print(f"Steps    :\n{result['action_steps']}")

print("\n" + "=" * 60)
print("Exercise complete! You built 3 chains using LangChain.")
print("Day 15: Wire these chains into real FastAPI endpoints.")
print("=" * 60)
