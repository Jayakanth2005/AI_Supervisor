# # agent/agent.py
# import requests, os

# BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# def make_call(caller_id: str, question: str):
#     resp = requests.post(f"{BACKEND}/create_call", json={"caller_id": caller_id, "question": question})
#     r = resp.json()
#     print("Agent received:", r)
#     return r

# if __name__ == "__main__":
#     # quick demo: run `python -m agent.agent` to simulate caller
#     make_call("caller_123", "Do you offer eyelash extensions?")
#     make_call("caller_123", "What are your hours?")


import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
CALLER_ID = os.getenv("CALLER_ID", "caller-1")


def make_call(question: str):
    payload = {"caller_identity": CALLER_ID, "question": question}
    r = requests.post(f"{BACKEND}/help-requests", json=payload)
    if r.status_code == 201:
        print("Created help request:", r.json())
    else:
        print("Create failed:", r.status_code, r.text)    


def poll_requests():
    r = requests.get(f"{BACKEND}/help-requests")
    if r.ok:
        items = r.json()
        print("All help requests:")
        for it in items:
            print(it)
    else:
        print("Failed to fetch requests", r.text)


def poll_learned():
    r = requests.get(f"{BACKEND}/learned-answers")
    if r.ok:
        items = r.json()
        print("Learned answers:")
        for it in items:
            print(it)
    else:
        print("No learned answers yet.")


if __name__ == "__main__":
    print("Agent simulator: creating two sample calls...")
    make_call("Do you offer eyelash extensions?")
    make_call("What are your hours?")

    # Poll for updates a few times to show workflow
    for i in range(8):
        poll_requests()
        poll_learned()
        time.sleep(4)
