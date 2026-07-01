# =============================================================================
# Day 11 — Exercise: Calling External APIs
# Free API used: JSONPlaceholder (https://jsonplaceholder.typicode.com)
# No API key needed!
# =============================================================================
# Instructions:
#   Work through each TODO. Run the file after each block.
#   Refer to day11_api_basics.py if you get stuck.
# =============================================================================

import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://jsonplaceholder.typicode.com"

# ─────────────────────────────────────────────
# EXERCISE 1 — Basic GET request
# ─────────────────────────────────────────────
print("=" * 50)
print("EXERCISE 1 — Basic GET")
print("=" * 50)

# TODO 1a: Make a GET request to BASE_URL + "/posts/1"
#          Store the response in a variable called `response`
# your code here
response = requests.get(BASE_URL + "/posts/1")
print(f"{response.text}")

# TODO 1b: Print the status code
# your code here
print(f"{response.status_code}")

# TODO 1c: Parse the JSON and print the title field
# your code here
print(f"{response.json()}")


# ─────────────────────────────────────────────
# EXERCISE 2 — GET with query parameters
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 2 — GET with Query Params")
print("=" * 50)

# TODO 2a: GET all posts for userId=2, limit to 4 results
#          Hint: params={"userId": 2, "_limit": 4}
# your code here
params={"userId": 2, "_limit": 4}
response = requests.get(BASE_URL + "/posts", params=params)
result = response.json()
print(f"{result}");

# TODO 2b: Print how many posts you got back
# your code here
print(f"{len(result)}")

# TODO 2c: Loop through and print each post's id and title
# your code here
for val in result:
    print(f"Id: {val["id"]} Title:{val["title"]}")



# ─────────────────────────────────────────────
# EXERCISE 3 — POST request
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 3 — POST Request")
print("=" * 50)

# TODO 3a: POST a new post to BASE_URL + "/posts"
#          Body should have: title, body, userId
# your code here
payload ={"title":"Buy Groceriris", "body":" to do", "userId":"1234"} 
response = requests.post(BASE_URL + "/posts", json=payload)

# TODO 3b: Print the status code (should be 201)
# your code here
print(f"{response.status_code}")
# TODO 3c: Print the full response JSON
# your code here
print(f"{response.json()}")


# ─────────────────────────────────────────────
# EXERCISE 4 — Error handling
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 4 — Error Handling")
print("=" * 50)

# TODO 4a: Write a function called `get_post(post_id)`
#          - Makes a GET request to /posts/{post_id}
#          - Uses try/except to handle errors
#          - Calls raise_for_status()
#          - Returns the JSON dict on success, None on failure
# your code here
def get_post(post_id):
    try:
        response = requests.get(BASE_URL + f"/posts/{post_id}",timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"Failed to fetch {post_id}: {e}")
        return None      
    



# TODO 4b: Call get_post(3) and print the title
# your code here
print(f"{get_post(3)["title"]}")


# TODO 4c: Call get_post(99999) — should return None gracefully
# your code here
print(f"{get_post(9999)}")


# ─────────────────────────────────────────────
# EXERCISE 5 — Bonus: Comments on a post
# ─────────────────────────────────────────────
print("\n" + "=" * 50)
print("EXERCISE 5 — Bonus")
print("=" * 50)

# TODO 5a: GET all comments for postId=1
#          URL: BASE_URL + "/comments" with params={"postId": 1}
# your code here
response= requests.get(url= BASE_URL + "/comments", params={"postId": 1})
result = response.json()

# TODO 5b: Print how many comments the post has
# your code here
print(f"{len(result)}")

# TODO 5c: Print just the name and email of each commenter
# your code here
for val in result:
    print(f"name {val["name"]} email{val["email"]}")

print("\nExercise complete!")
