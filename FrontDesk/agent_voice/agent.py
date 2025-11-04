# from .speech import listen, speak
# import requests
# import os
# from dotenv import load_dotenv

# load_dotenv()
# BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# def run_voice_agent():
#     caller_name = input("Enter your name: ")
#     speak(f"Hello {caller_name}, how can I help you today?")
#     while True:
#         question = listen()
#         if not question or "exit" in question.lower():
#             speak("Goodbye!")

#             break
#         res = requests.post(f"{BACKEND_URL}/help-requests", params={"caller_name": caller_name, "question": question})
#         speak("Your question has been sent to the backend.")


from .speech import listen, speak
import requests
import os
from dotenv import load_dotenv
import re



load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def backend_url(path: str) -> str:
    return BACKEND_URL.rstrip("/") + path


def kb_search(query: str, top_k: int = 3):
    """Query the backend KB for possible answers."""
    try:
        r = requests.get(backend_url("/kb/search"), params={"q": query, "top_k": top_k}, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ KB search failed: {e}")
        return []


def create_help_request(caller_name: str, question: str):
    """Send unresolved questions to backend."""
    try:
        payload = {"caller_name": caller_name, "question": question}
        r = requests.post(backend_url("/help-requests"), json=payload, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Failed to create help request: {e}")
        return None


def is_relevant(user_q, kb_q):
    """Simple relevance check based on common keywords."""
    user_words = set(re.findall(r"\w+", user_q.lower()))
    kb_words = set(re.findall(r"\w+", kb_q.lower()))
    stopwords = {"the", "is", "and", "a", "an", "to", "for", "in", "of", "on", "are", "you", "we", "do", "have"}
    overlap = (user_words - stopwords) & (kb_words - stopwords)
    return len(overlap) >= 2  # at least 2 common keywords = relevant


def run_voice_agent():
    caller_name = input("Enter your name: ")
    speak(f"Hello {caller_name}, how can I help you today?")

    while True:
        question = listen()
        if not question:
            continue
        if "exit" in question.lower():
            speak("Goodbye!")
            break

        print(f"🔍 Searching KB for: {question}")
        kb_results = kb_search(question, top_k=3)

        if not kb_results:
            speak("I couldn't find an answer in the knowledge base. Sending your question to the supervisor.")
            create_help_request(caller_name, question)
            continue

        top = kb_results[0]
        top_score = top.get("score", 0)
        top_question = top.get("question_pattern", "")
        top_answer = top.get("answer", "")

        # Adjust confidence threshold as needed
        kb_cutoff = 0.75
        if top_score >= kb_cutoff and is_relevant(question, top_question):
            print(f"✅ Confident KB match (score={top_score:.2f})")
            speak(f"Here's what I found: {top_answer}")
        else:
            print(f"⚠️ Low confidence (score={top_score:.2f}). Escalating.")
            speak("I'm not sure about the answer. Sending your question to the supervisor.")
            create_help_request(caller_name, question)


if __name__ == "__main__":
    run_voice_agent()
