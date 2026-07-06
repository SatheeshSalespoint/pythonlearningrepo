"""
Day 12 — Exercise: Personal Task Assistant Chatbot
====================================================
Goal: Build a chatbot that knows your tasks and answers questions about them.

Requirements:
1. Define a list of tasks (id, title, status, priority)
2. Build a system prompt that gives the AI your tasks as context
3. Start a while loop — user types a question, AI replies
4. Keep conversation history (multi-turn) — AI remembers previous questions
5. Type "quit" to exit

Expected conversation example:
  You: Which tasks are high priority?
  AI:  Tasks 1 and 4 are high priority...

  You: Which one should I do first?
  AI:  I recommend starting with "Fix login bug" because...

  You: quit
  AI:  Goodbye!

Hints:
- tasks list is already given to you below
- system_prompt should include the tasks (use str() or json.dumps())
- messages list starts with the system message
- inside the loop: get input → add to messages → call ollama.chat() → print reply → add reply to messages
"""

import ollama

MODEL = "qwen2.5-coder:7b"

# ---------------------------------------------------------------------------
# STEP 1: Your tasks data
# (Already done for you — focus on the AI part)
# ---------------------------------------------------------------------------
tasks = [
    {"id": 1, "title": "Fix login bug",       "status": "pending", "priority": "high"},
    {"id": 2, "title": "Write unit tests",    "status": "pending", "priority": "medium"},
    {"id": 3, "title": "Update API docs",     "status": "done",    "priority": "low"},
    {"id": 4, "title": "Deploy to staging",   "status": "pending", "priority": "high"},
    {"id": 5, "title": "Code review PR #42",  "status": "pending", "priority": "medium"},
]

# ---------------------------------------------------------------------------
# STEP 2: Build the system prompt
# Tell the AI: who it is + what tasks it knows about
# ---------------------------------------------------------------------------
# YOUR CODE HERE
# system_prompt = ???
system_prompt = f"You are a task management assistant... Here is the task list {tasks}"


# ---------------------------------------------------------------------------
# STEP 3: Start the messages list with the system message
# ---------------------------------------------------------------------------
# YOUR CODE HERE
# messages = ???
messages = [
    {"role": "system", "content": system_prompt}    
]


# ---------------------------------------------------------------------------
# STEP 4: Print a welcome message so the user knows the chatbot is ready
# ---------------------------------------------------------------------------
# YOUR CODE HERE
print("Task Assistant ready! Ask me anything about your tasks. Type 'quit' to exit.")


# ---------------------------------------------------------------------------
# STEP 5: Start the chat loop
# ---------------------------------------------------------------------------
# while True:
#     1. Get input from user  →  user_input = input("You: ")
#     2. If user typed "quit" → print goodbye and break
#     3. Add user message to messages list
#     4. Call ollama.chat()
#     5. Get reply from response.message.content
#     6. Print the reply
#     7. Add the reply to messages list (so AI remembers it next turn)

# YOUR CODE HERE

while True: 
    user_input = input("You:")
    if(user_input.lower()== "quit"):
        print("Good Bye")
        break
    messages.append({"role":"user","content":user_input})
    response = ollama.chat(model = MODEL, messages= messages)
    reply = response.message.content
    print("AI:",reply)
    messages.append({"role":"assistant", "content":reply})