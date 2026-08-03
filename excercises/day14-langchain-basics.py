"""
Day 14 — LangChain Basics
=========================
Topics:
  - What is LangChain and why use it over raw API calls
  - ChatPromptTemplate — reusable prompt templates with variables
  - ChatOllama — LangChain wrapper for your local Ollama model
  - Chain (|) — composing prompt → LLM → output parser
  - StrOutputParser — extract plain text from AI response
  - Building a simple summariser chain

Run: python day14-langchain-basics.py
Requires: Ollama running locally with qwen2.5-coder:7b pulled
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama


# ── 1. Create the LLM ────────────────────────────────────────────────────────
# ChatOllama = LangChain wrapper around your local Ollama model
# C# analogy: like a typed HttpClient configured for a specific base URL
llm = ChatOllama(model="qwen2.5-coder:7b", temperature=0.3)


# ── 2. Create a Prompt Template ──────────────────────────────────────────────
# ChatPromptTemplate.from_messages() = define your conversation structure
# {task_title} is a placeholder — filled in when you call .invoke()
# C# analogy: like $"Hello {name}" but for multi-message AI conversations
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful task assistant. Give short, clear responses."),
    ("user", "Summarise this task in one sentence: {task_title}")
])


# ── 3. Build a Chain ─────────────────────────────────────────────────────────
# The | (pipe) operator chains steps together: prompt → llm → output parser
# C# analogy: like LINQ — source.Select(...).Where(...) — each step transforms data
# StrOutputParser() extracts the plain text string from the AI's response object
chain = prompt | llm | StrOutputParser()


# ── 4. Run the Chain ─────────────────────────────────────────────────────────
# .invoke() fills in the template variables and runs the full chain
print("=" * 50)
print("EXAMPLE 1 — Single task summary")
print("=" * 50)

result = chain.invoke({"task_title": "Fix the login bug that causes users to be logged out after 5 minutes"})
print(f"Summary: {result}")


# ── 5. Reusing the same chain with different inputs ──────────────────────────
# This is the power of LangChain — define once, call many times
print("\n" + "=" * 50)
print("EXAMPLE 2 — Reuse chain for multiple tasks")
print("=" * 50)

tasks = [
    "Update the database schema to add a new 'priority' column to the tasks table",
    "Write unit tests for the user authentication module",
    "Deploy the new API version to the production server",
]

for task in tasks:
    summary = chain.invoke({"task_title": task})
    print(f"• {summary}")


# ── 6. Multi-variable template ───────────────────────────────────────────────
# Templates can have multiple placeholders — like method parameters in C#
print("\n" + "=" * 50)
print("EXAMPLE 3 — Multi-variable prompt template")
print("=" * 50)

priority_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a project manager. Respond with ONLY one word: High, Medium, or Low."),
    ("user", "Task: {task_title}\nDeadline: {deadline}\nWhat priority should this task be?")
])

priority_chain = priority_prompt | llm | StrOutputParser()

priority = priority_chain.invoke({
    "task_title": "Fix critical security vulnerability in the login system",
    "deadline": "Tomorrow"
})
print(f"Suggested priority: {priority}")


# ── 7. Inspecting the prompt before sending ──────────────────────────────────
# Useful for debugging — see what gets sent to the LLM
print("\n" + "=" * 50)
print("EXAMPLE 4 — Inspect formatted prompt (debugging)")
print("=" * 50)

formatted = prompt.format_messages(task_title="Review pull request #42")
for message in formatted:
    print(f"[{message.type.upper()}]: {message.content}")

print("\nDay 14 - Part 1 complete! Core concepts done.")
print("Next: Build the exercise - task summariser chain with multiple features")
