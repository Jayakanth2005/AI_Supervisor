
---

# 6) Notes on design decisions (short, per spec)

- **Modeling help requests**: single `HelpRequest` table with lifecycle fields and timestamps. This is simple, clear, and easily extensible (we can add `customer_contact` later).
- **Supervisor notification**: For demo we simulate notification. In production you'd call Twilio, Slack webhook, or LiveKit DataChannel to notify.
- **Knowledge base updates**: This demo records `supervisor_response`. To implement a KB, you would store the Q/A in a `learned_answers` table and integrate a local similarity search to answer future similar queries automatically.
- **Scaling**: DB is SQLite for demo; for 1k/day use DynamoDB / Postgres. Background workers (Redis + RQ/Celery) for webhooks, retries, and follow-up sending.
- **LiveKit**: We use LiveKit tokens created server-side. The browser publishes microphone audio so the audition is audible to other participants.

---

# 7) Full code recap (copy-paste ready)

I already listed the main files above. To make it easy I'll provide a ZIP-friendly overview: create folders and paste each file content placed in the right path.

- `backend/__init__.py` — can be empty.
- `backend/models.py` — as above.
- `backend/db.py` — as above.
- `backend/livekit_token.py` — as above.
- `backend/main.py` — the FastAPI app content above plus the `StaticFiles` mount (copy the earlier `main.py` and add the static mount snippet).
- `backend/requirements.txt` — earlier.
- `backend/.env.example` — earlier.

- `agent/index.html` — earlier.
- `agent/agent.js` — earlier.

- `supervisor_ui/app.py` — earlier.
- `supervisor_ui/requirements.txt` — earlier.

- `README.md` — earlier.

---

# 8) How to demo (explicit checklist for the assessment)

1. Add LiveKit credentials to `backend/.env`.
2. Start backend:


# FrontDesk Human-in-the-Loop Demo

## Overview
This project demonstrates a minimal human-in-the-loop for a voice agent using LiveKit (voice), a FastAPI backend to store help requests, and a small Streamlit supervisor UI. The agent is a browser client that uses LiveKit JS and browser TTS.

## Requirements
- Python 3.10+ recommended
- pip, node not required (static)
- LiveKit account (cloud or self-hosted) **(REQUIRED for LiveKit demo)**:
  - LIVEKIT_URL
  - LIVEKIT_API_KEY
  - LIVEKIT_API_SECRET

If you do not have LiveKit and want to demo logic only, set `SIMULATE_LIVEKIT=true` in `.env` and the agent will still speak locally but will not connect to a LiveKit room.

## Setup (Backend)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and set LIVEKIT_URL/KEY/SECRET (or set SIMULATE_LIVEKIT=true)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
