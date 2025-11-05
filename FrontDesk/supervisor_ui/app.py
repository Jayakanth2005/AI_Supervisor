
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import streamlit as st
import requests
from dotenv import load_dotenv
from typing import Optional
import re 
from agent_voice.speech import speak
import speech_recognition as sr



load_dotenv()  # loads supervisor_ui/.env if present, or project root .env

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Utility function to build absolute backend endpoints
def backend_url(path: str) -> str:
    """Create a fully qualified backend URL from a path like '/help-requests'."""
    return BACKEND_URL.rstrip("/") + path

st.set_page_config(page_title="FrontDesk Supervisor UI", layout="wide")
st.title("FrontDesk — Supervisor / Agent Simulator")

st.caption("A simple Streamlit admin for the human-in-the-loop demo. Use Supervisor to answer pending requests. Use Agent Simulator to create new requests or request LiveKit tokens.")

# -------------------------
# Simple top row with config
# -------------------------
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.markdown("**Backend endpoint:**")
    st.code(BACKEND_URL, language="bash")
with col2:
    st.markdown("**Run instructions**")
    st.write("1. Start backend (FastAPI) at the address above. 2. Start agent static site if needed. 3. Use these tabs.")
with col3:
    # Button to refresh the app
    if st.button("Hard refresh UI"):
        try:
            st.rerun()
        except Exception:
            st.info("Please manually refresh the page.")

# -------------------------
# Tabs: Supervisor | Agent Simulator
# -------------------------
tabs = st.tabs(["Supervisor", "Agent Simulator", "Logs / Debug"])

# -------------------------
# Helper functions (API wrappers)
# -------------------------
def fetch_requests(status: Optional[str] = None):
    """
    Fetch help requests from backend.
    If status is provided, backend will filter by that (pending/resolved/unresolved).
    """
    try:
        params = {}
        if status:
            params["status"] = status
        resp = requests.get(backend_url("/help-requests"), params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch requests: {e}")
        return []

def get_request_by_id(req_id: int):
    """
    Helper to fetch a single request from the list (backend doesn't provide /help-requests/{id} GET in the minimal API),
    so we re-fetch all and filter locally.
    """
    rows = fetch_requests()
    for r in rows:
        if r["id"] == req_id:
            return r
    return None

def post_supervisor_response(req_id: int, response_text: str, status: str, save_to_kb: bool = False):
    """
    Post the supervisor response to backend. Expects SupervisorAnswer model:
    { supervisor_response: str, status: "resolved"|"unresolved", save_to_kb: bool (optional) }
    """
    payload = {"supervisor_response": response_text, "status": status}
    # include save_to_kb only if True to remain compatible with older backends
    if save_to_kb:
        payload["save_to_kb"] = True
    r = requests.post(backend_url(f"/help-requests/{req_id}/respond"), json=payload, timeout=8)
    r.raise_for_status()
    return r.json()

def trigger_agent_followup(req_id: int):
    """Call backend endpoint to simulate agent following up the original caller."""
    r = requests.post(backend_url(f"/help-requests/{req_id}/agent-followup"), timeout=8)
    r.raise_for_status()
    return r.json()

def create_help_request(caller_name: str, question: str, livekit_room: Optional[str] = None):
    """Call backend to create a help request (simulating agent escalation)."""
    payload = {"caller_name": caller_name, "question": question, "livekit_room": livekit_room}
    r = requests.post(backend_url("/help-requests"), json=payload, timeout=8)
    r.raise_for_status()
    return r.json()

def request_livekit_token(identity: str, room: Optional[str] = None):
    """Request a token from backend /token?identity=...&room=..."""
    params = {"identity": identity}
    if room:
        params["room"] = room
    r = requests.post(backend_url("/token"), params=params, timeout=8)
    r.raise_for_status()
    return r.json()

# -------------------------
# Knowledge Base helpers
# -------------------------
def kb_search(query: str, top_k: int = 3):
    """Query backend KB search endpoint: /kb/search?q=..."""
    try:
        r = requests.get(backend_url("/kb/search"), params={"q": query, "top_k": top_k}, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"KB search failed: {e}")
        return []

def list_kb():
    """List all learned answers via GET /learned-answers"""
    try:
        r = requests.get(backend_url("/learned-answers"), timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to fetch KB entries: {e}")
        return []

# -------------------------
# Tab: Supervisor
# -------------------------
with tabs[0]:
    st.header("Supervisor Panel")

    # Filter controls
    left, right = st.columns([2, 3])
    with left:
        status_filter = st.selectbox("Filter by status", options=["pending", "resolved", "unresolved", "all"], index=0)
        if st.button("Refresh list"):
            try:
                st.rerun()
            except Exception:
                st.info("Please manually refresh the page.")
    with right:
        st.write("Click a request to open details below and respond.")

    # Fetch requests from backend
    requests_list = fetch_requests(None if status_filter == "all" else status_filter)

    st.subheader(f"Requests ({len(requests_list)})")
    # Display summary table (two columns)
    for req in requests_list:
        # Each request is displayed in an expander for compactness.
        created_at_str = req.get("created_at", "")[:19] if req.get("created_at") else ""
        with st.expander(f"ID {req['id']} — {req['caller_name']} — {req['status']} — created {created_at_str}", expanded=False):
            st.write("**Question:**")
            st.write(req["question"])
            st.write("---")
            st.write(f"**Supervisor response:** {req.get('supervisor_response')}")
            st.write(f"**Follow-up sent:** {req.get('follow_up_sent')}")
            # Buttons to act on this request
            c1, c2, c3 = st.columns([2, 2, 2])
            with c1:
                if st.button(f"Open in pane (ID {req['id']})", key=f"open-{req['id']}"):
                    # Show full details in the response pane below by st.session_state
                    st.session_state.setdefault("selected_request", req["id"])
                    try:
                        st.rerun()
                    except Exception:
                        st.info("Please manually refresh to see changes.")
            with c2:
                if st.button(f"Trigger follow-up (ID {req['id']})", key=f"fu-{req['id']}"):
                    try:
                        fu = trigger_agent_followup(req["id"])
                        st.success(f"Follow-up: {fu.get('follow_up')}")
                        try:
                            st.rerun()
                        except Exception:
                            pass
                    except Exception as e:
                        st.error(f"Follow-up failed: {e}")
            with c3:
                # Provide a quick "copy" option for livekit room name (if present)
                room = req.get("livekit_room")
                if room:
                    st.write("LiveKit room:")
                    st.code(room)
                else:
                    st.write("No LiveKit room attached.")

    st.markdown("---")
    # Detailed response pane for selected request (if any)
    sel_id = st.session_state.get("selected_request")
    if sel_id:
        st.subheader(f"Respond to request {sel_id}")
        selected = get_request_by_id(sel_id)
        if not selected:
            st.error("Selected request is no longer available. Refresh.")
        else:
            st.write(f"**Caller:** {selected['caller_name']}")
            st.write(f"**Question:** {selected['question']}")
            default_answer = selected.get("supervisor_response") or ""
            answer_text = st.text_area("Your response", value=default_answer, height=150)
            status_choice = st.selectbox("Set status", options=["resolved", "unresolved"], index=0)
            save_to_kb = st.checkbox("Save this response to Knowledge Base (learned answer)", value=True)
            if st.button("Submit response", key=f"submit-{sel_id}"):
                try:
                    post_supervisor_response(sel_id, answer_text, status_choice, save_to_kb)
                    st.success("Response recorded. You can trigger follow-up now.")
                    # Optionally trigger follow-up automatically
                    if st.checkbox("Trigger agent follow-up automatically after response", value=True):
                        fu = trigger_agent_followup(sel_id)
                        st.info(f"Agent follow-up: {fu.get('follow_up')}")
                    # Clear selection and refresh UI
                    st.session_state.pop("selected_request", None)
                    try:
                        st.rerun()
                    except Exception:
                        st.info("Please manually refresh to see updated list.")
                except Exception as e:
                    st.error(f"Failed to submit response: {e}")

# -------------------------
# Tab: Agent Simulator
# -------------------------
with tabs[1]:
    st.header("Agent Simulator (KB-first)")
    st.markdown(
        "When a client question arrives, the agent will **first search the Knowledge Base**. "
        "If a matching learned answer is found you can simulate replying with it. "
        "Otherwise a help request will be created."
    )

    # Input fields to create a help request
    col_a, col_b = st.columns([2, 4])
with col_a:
    caller_name = st.text_input("Caller name", value="Alice")
    room_name = st.text_input("Optional: LiveKit room name", value="")
    kb_cutoff = st.slider(
        "KB auto-reply threshold (0-1)",
        min_value=0.0,
        max_value=1.0,
        value=0.75,
        step=0.05,
        help="If KB match score >= threshold, treat as confident answer and don't escalate."
    )

with col_b:
    st.write("**🎙️ Speak your question**")

    if "voice_input" not in st.session_state:
        st.session_state.voice_input = ""

    if st.button("🎤 Record / Stop Voice"):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening... Speak now.")
            try:
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                st.info("Processing your voice...")
                text = r.recognize_google(audio)
                st.session_state.voice_input = text
                st.success(f"Recognized: {text}")

                # Confirm what was heard
                speak(f"You said: {text}")

                # 🔹 Auto-check Knowledge Base
                st.info("Checking Knowledge Base for an answer...")
                kb_results = kb_search(text, top_k=5)

                if not kb_results:
                    st.warning("No KB entries found. Escalating to supervisor.")
                    speak("I don’t know the answer. Forwarding this to the supervisor.")
                    try:
                        r = create_help_request(caller_name, text, livekit_room=room_name or None)
                        st.success(f"Created help request ID: {r.get('id')}")
                    except Exception as e:
                        st.error(f"Failed to create help request: {e}")
                    st.stop()

                # Function to check basic relevance
                def is_relevant(user_q, kb_q):
                    import re
                    user_words = set(re.findall(r"\w+", user_q.lower()))
                    kb_words = set(re.findall(r"\w+", kb_q.lower()))
                    stopwords = {"the", "is", "and", "a", "an", "to", "for", "in", "of", "on", "are", "you", "we", "do", "have"}
                    overlap = (user_words - stopwords) & (kb_words - stopwords)
                    return len(overlap) >= 2

                # Analyze top KB match
                top = kb_results[0]
                top_score = top.get("score", 0)
                top_question = top.get("question_pattern", "")
                top_answer = top.get("answer", "")

                # Decide based on confidence
                if top_score >= kb_cutoff and is_relevant(text, top_question):
                    st.success(f"KB match confident (score {top_score:.2f}) — replying automatically.")
                    st.info(f"Agent reply: {top_answer}")
                    speak(f"Here's what I found: {top_answer}")
                else:
                    st.warning("Low confidence. Escalating to supervisor.")
                    speak("I’m not sure about that. I’ll forward this question to the supervisor.")
                    try:
                        r = create_help_request(caller_name, text, livekit_room=room_name or None)
                        st.success(f"Help request ID {r.get('id')} created.")
                    except Exception as e:
                        st.error(f"Failed to create help request: {e}")

            except sr.WaitTimeoutError:
                st.warning("No voice detected, please try again.")
            except sr.UnknownValueError:
                st.error("Sorry, I couldn't understand that.")
            except Exception as e:
                st.error(f"Error: {e}")

    # Text area auto-fills with recognized or typed question
    question = st.text_area(
        "Customer question",
        value=st.session_state.get("voice_input", "Do you have an appointment tomorrow morning?")
    )



    c1, c2, c3 = st.columns([1, 1, 1])

    # ✅ keep all logic indented under the same tab
    with c1:

        def is_relevant(user_q, kb_q):
            """Simple relevance check based on common keywords."""
            user_words = set(re.findall(r"\w+", user_q.lower()))
            kb_words = set(re.findall(r"\w+", kb_q.lower()))
            stopwords = {"the", "is", "and", "a", "an", "to", "for", "in", "of", "on", "are", "you", "we", "do", "have"}
            overlap = (user_words - stopwords) & (kb_words - stopwords)
            return len(overlap) >= 2  # at least 2 common keywords = relevant

        if st.button("Check KB & (maybe) escalate"):
            kb_results = kb_search(question, top_k=5)

            if not kb_results:
                st.info("No KB matches found. Creating help request.")
                try:
                    r = create_help_request(caller_name, question, livekit_room=room_name or None)
                    st.success(f"Created new help request ID: {r.get('id')}")
                    st.write("Now switch to Supervisor tab to respond.")
                    speak("I could not find an answer. I have sent your question to the supervisor.")  # 👈 Voice feedback
                except Exception as e:
                    st.error(f"Failed to create help request: {e}")
                st.stop()

            # Show KB results
            st.info("KB suggestions (best first):")
            for i, s in enumerate(kb_results):
                st.markdown(f"**#{i+1} - score {s.get('score', 0):.2f}**")
                st.write("Pattern:", s.get("question_pattern"))
                st.write("Answer:", s.get("answer"))
                st.write("---")

            top = kb_results[0]
            top_score = top.get("score", 0)
            top_question = top.get("question_pattern", "")
            top_answer = top.get("answer", "")

            if top_score >= kb_cutoff and is_relevant(question, top_question):
                st.success(f"Top KB match is confident (score {top_score:.2f}). Agent can auto-reply.")
                st.info("Agent replied with:")
                st.write(top_answer)
                speak(f"Here's what I found: {top_answer}")  # Voice feedback (non-blocking)
            else:
                st.warning(f"Low confidence (score {top_score:.2f}). Escalating to Supervisor.")
                try:
                    r = create_help_request(caller_name, question, livekit_room=room_name or None)
                    st.success(f"Created help request ID: {r.get('id')}")
                    st.info("Supervisor will review this soon.")
                    speak("I'm not sure about the answer. Sending your question to the supervisor.")
                except Exception as e:
                    st.error(f"Failed to create help request: {e}")


    with c2:
        if st.button("Request LiveKit token (for agent)"):
            try:
                # Use the caller name as identity for demo
                token_resp = requests.get(backend_url(f"/token?identity=agent-{caller_name}&room={room_name or ''}"), timeout=8)
                token_resp.raise_for_status()
                token_json = token_resp.json()
                st.success("Token acquired")
                st.write("LiveKit URL & token (keep secret):")
                st.code(token_json)
                st.write("You can open your agent static page and pass this token or just use it to debug.")
            except Exception as e:
                st.error(f"Failed to request token: {e}")
    with c3:
        if st.button("Clear created requests (dev only)"):
            st.warning("No backend endpoint provided to delete all requests in demo; implement backend delete if needed.")

    st.markdown("---")
    st.write("Quick log: Last 5 pending requests")
    pending = fetch_requests("pending")
    if not pending:
        st.info("No pending requests found.")
    else:
        for r in pending[-5:]:
            st.write(f"ID {r['id']} — {r['caller_name']} — {r['question'][:80]}...")

# -------------------------
# Tab: Logs / Debug
# -------------------------
with tabs[2]:
    st.header("Logs / Debug")
    st.write("This page is for quick debugging and manual requests.")
    st.subheader("Backend health check")
    try:
        health = requests.get(backend_url("/help-requests"), timeout=5)
        st.success(f"Backend reachable (GET /help-requests returned {health.status_code})")
    except Exception as e:
        st.error(f"Backend unreachable: {e}")

    st.markdown("**Manual API tester**")
    method = st.selectbox("Method", options=["GET", "POST"])
    path = st.text_input("Path (e.g. /help-requests or /token?identity=me)", value="/help-requests")
    body = st.text_area("JSON body (for POST)", value='{"caller_name":"Bob","question":"Test?"}')
    if st.button("Send manual request"):
        url = backend_url(path)
        try:
            if method == "GET":
                r = requests.get(url, timeout=8)
            else:
                # try parse JSON body, fallback to raw string
                try:
                    import json
                    parsed = json.loads(body)
                except Exception:
                    parsed = body
                r = requests.post(url, json=parsed, timeout=8)
            st.write("Status:", r.status_code)
            st.json(r.json())
        except Exception as e:
            st.error(f"Request failed: {e}")

    st.markdown("---")
    st.subheader("Learned Answers (KB) preview")
    try:
        kb_entries = list_kb()
        if not kb_entries:
            st.info("No KB entries yet.")
        else:
            for e in kb_entries[-30:]:
                st.write(f"ID {e.get('id')} — source {e.get('source')} — created {e.get('created_at')}")
                st.write("Q:", e.get('question_pattern'))
                st.write("A:", e.get('answer'))
                st.write("---")
    except Exception as e:
        st.error(f"Failed to fetch KB entries: {e}")










