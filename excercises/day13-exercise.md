# Day 13 — Prompt Engineering 🧠

**Goal:** Learn how to write prompts that get great results from an LLM.

---

## What is Prompt Engineering?

When you call an LLM, the quality of the output depends almost entirely on HOW you write the prompt.

Think of it like writing a specification for a junior developer:
- A vague spec → vague result
- A clear, structured spec with examples → exactly what you want

**C# analogy:** It's like the difference between writing a vague comment `// do the thing` vs a proper XML doc comment with parameter descriptions and examples.

---

## Concept 1 — Zero-Shot Prompting

**What it is:** You give the AI a task with NO examples. Just instructions.

**When to use:** Simple tasks where the AI already knows how to do it.

```python
# Zero-shot — no examples, just the instruction
prompt = "Classify this task as High, Medium, or Low priority: 'Fix login bug'"
```

**Output:** `High`

---

## Concept 2 — Few-Shot Prompting

**What it is:** You give the AI 2–5 examples of input → output BEFORE your real question.

**When to use:** When you want consistent formatting or when the AI needs to learn YOUR pattern.

```python
# Few-shot — you show examples first, then ask
prompt = """
Classify each task as High, Medium, or Low priority.

Examples:
Task: "Fix login bug" → High
Task: "Update homepage text" → Low
Task: "Database migration failing in prod" → High
Task: "Add dark mode" → Medium

Now classify this:
Task: "Users can't reset their password" → 
"""
```

**Why it's better:** The AI now knows YOUR definition of priority, not just its own guess.

**C# analogy:** Like providing unit test examples to show what "correct" looks like before asking for implementation.

---

## Concept 3 — Chain-of-Thought (CoT) Prompting

**What it is:** You tell the AI to **think step by step** before giving the answer.

**When to use:** Complex reasoning, analysis, or multi-step decisions.

```python
# Without CoT — may give wrong answer
prompt = "Should I prioritise task A (fix login) or task B (add analytics)?"

# With CoT — forces reasoning first
prompt = """
I have two tasks:
- Task A: Fix login bug (affects all users, production issue)
- Task B: Add analytics dashboard (nice to have, no users affected)

Think step by step about which to prioritise, then give your recommendation.
"""
```

**Why it's better:** Forces the AI to reason, not just react. Dramatically improves accuracy on complex decisions.

---

## Concept 4 — System Prompts (Role Prompting)

**What it is:** You set the AI's **role, personality, and rules** in the system message.

**When to use:** Always — for any serious AI application.

```python
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
```

**C# analogy:** The system prompt is like your app's `appsettings.json` + dependency injection setup — it configures the AI's behaviour before any real work starts.

---

## Concept 5 — Prompt Templates (Dynamic Prompts)

**What it is:** Reusable prompt patterns with **variables** filled in at runtime using f-strings.

**When to use:** When you call the AI with different data each time (your real-world use case).

```python
def build_priority_prompt(task_title: str, task_description: str, context: str) -> str:
    return f"""
You are a software project manager.

Analyse this task and suggest a priority (High/Medium/Low).

Task Title: {task_title}
Description: {task_description}
Context: {context}

Respond ONLY with JSON in this format:
{{"priority": "High", "reason": "one sentence explanation"}}
"""
```

---

## 🏋️ Exercise

**File to create:** `excercises/day13-prompt-engineering.py`

### Part 1 — Zero-shot vs Few-shot comparison
Write two versions of a prompt that classifies a task priority.  
Compare the outputs — does few-shot give better/more consistent results?



### Part 2 — Chain-of-thought
Write a CoT prompt that asks the AI to decide which of two tasks to do first.  
Ask it to "think step by step" before answering.

### Part 3 — Prompt template function
Write a `build_prompt(task: dict) -> str` function that builds a consistent prompt  
from a task dictionary `{"title": "...", "description": "...", "status": "..."}`.

### Part 4 — System prompt + few-shot combined (Stretch Goal)
Combine a system prompt (role + rules) with few-shot examples.  
Get the AI to always respond in JSON: `{"priority": "...", "reason": "..."}`.

---

## Key Rules to Remember

| Rule | Why |
|------|-----|
| Be specific — tell the AI exactly what format you want | Prevents rambling or wrong structure |
| Use examples (few-shot) for consistent output | AI learns YOUR pattern |
| Use "think step by step" for complex decisions | Improves reasoning accuracy |
| Always set a system prompt in real apps | Controls AI behaviour and output format |
| Keep prompts in functions — never hardcode in endpoint logic | Reusable, testable, maintainable |
