"""
Day 12 — LLM API Basics with Ollama
====================================
Goal: Understand how to talk to an LLM programmatically.
      Same concepts as OpenAI API — transfers directly when you get a key.

Model used: qwen2.5-coder:7b (running locally via Ollama)
"""

import ollama

MODEL = "qwen2.5-coder:7b"

# ===========================================================================
# SECTION 1: The simplest possible LLM call
# ===========================================================================
# ollama.chat() sends a list of messages and returns a response.
# Each message has a "role" and "content".

print("=" * 60)
print("SECTION 1: Simplest LLM call")
print("=" * 60)

response = ollama.chat(
    model=MODEL,
    messages=[
        {"role": "user", "content": "What is 2 + 2? Answer in one word."}
    ]
)

# The reply is inside response.message.content
print("Answer:", response.message.content)


# ===========================================================================
# SECTION 2: The system role — giving the AI a persona/rules
# ===========================================================================
# system message = constructor/config for the AI
# It sets personality, language, constraints, output format etc.
# It is ALWAYS the first message in the list.

print("\n" + "=" * 60)
print("SECTION 2: System role — giving the AI a persona")
print("=" * 60)

response = ollama.chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a helpful task management assistant. "
                "Always respond in bullet points. "
                "Keep responses short and practical."
            )
        },
        {
            "role": "user",
            "content": "How should I prioritise my tasks today?"
        }
    ]
)

print(response.message.content)


# ===========================================================================
# SECTION 3: Multi-turn conversation (assistant role)
# ===========================================================================
# To have a back-and-forth conversation, you include PREVIOUS replies
# in the messages list using role="assistant".
# The model has no memory — you must send the full history each time.

print("\n" + "=" * 60)
print("SECTION 3: Multi-turn conversation")
print("=" * 60)

messages = [
    {"role": "system", "content": "You are a concise Python tutor."},
    {"role": "user", "content": "What is a list in Python?"},
]

# Turn 1
response = ollama.chat(model=MODEL, messages=messages)
turn1_reply = response.message.content
print("Turn 1 — AI:", turn1_reply)

# Add AI reply to history, then ask a follow-up
messages.append({"role": "assistant", "content": turn1_reply})
messages.append({"role": "user", "content": "How is it different from a tuple?"})

# Turn 2 — model sees full history, so it understands the context
response = ollama.chat(model=MODEL, messages=messages)
print("\nTurn 2 — AI:", response.message.content)


# ===========================================================================
# SECTION 4: Temperature — controlling randomness
# ===========================================================================
# options={"temperature": 0.0} = deterministic (same answer every time)
# options={"temperature": 0.7} = balanced
# options={"temperature": 1.2} = creative/varied

print("\n" + "=" * 60)
print("SECTION 4: Temperature (same prompt, two settings)")
print("=" * 60)

prompt = "Give me one creative name for a task management app."

# Low temperature — predictable
response_low = ollama.chat(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    options={"temperature": 0.0}
)
print("Temperature 0.0 ->", response_low.message.content.strip())

# Higher temperature — more creative
response_high = ollama.chat(
    model=MODEL,
    messages=[{"role": "user", "content": prompt}],
    options={"temperature": 1.0}
)
print("Temperature 1.0 ->", response_high.message.content.strip())


# ===========================================================================
# SECTION 5: Structured output — asking for JSON
# ===========================================================================
# You can instruct the AI to respond in a specific format.
# This is the foundation of AI-powered API endpoints.

print("\n" + "=" * 60)
print("SECTION 5: Asking for structured JSON output")
print("=" * 60)

response = ollama.chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a task classifier. "
                "Always respond with valid JSON only — no extra text. "
                "Format: {\"priority\": \"high|medium|low\", \"reason\": \"<short reason>\"}"
            )
        },
        {
            "role": "user",
            "content": "Task: Fix critical login bug that blocks all users."
        }
    ],
    options={"temperature": 0.0}
)

print("Raw response:", response.message.content)

# Parse the JSON response
import json
try:
    data = json.loads(response.message.content)
    print("Priority:", data["priority"])
    print("Reason:  ", data["reason"])
except json.JSONDecodeError:
    print("(Model didn't return clean JSON — try again or adjust the prompt)")


print("\nDay 12 basics complete!")
