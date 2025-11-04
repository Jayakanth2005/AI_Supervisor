




# backend/main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import select
from dotenv import load_dotenv
import os
from datetime import datetime
import difflib

from backend.db import init_db, get_session
from backend.models import HelpRequest, KnowledgeBase
from backend.livekit_token import generate_join_token  # uses your livekit token implementation

load_dotenv()

app = FastAPI(title="FrontDesk Human-in-loop Backend (with KB)")
init_db()

# -------------------------
# Pydantic payload models
# -------------------------
class CreateHelpRequest(BaseModel):
    caller_name: str
    question: str
    livekit_room: Optional[str] = None

class SupervisorAnswer(BaseModel):
    supervisor_response: str
    status: str  # "resolved" or "unresolved"
    save_to_kb: Optional[bool] = False  # optional flag to explicitly save to KB

class KBCreate(BaseModel):
    question_pattern: str
    answer: str
    source: Optional[str] = "MANUAL"

# -------------------------
# Helper: KB fuzzy search
# -------------------------
def find_kb_matches(query: str, top_k: int = 3, cutoff: float = 0.45):
    """
    Simple fuzzy search against KnowledgeBase.question_pattern values.
    Returns a list of dicts with id, question_pattern, answer, score, source.
    """
    with get_session() as session:
        rows = session.exec(select(KnowledgeBase)).all()
        if not rows:
            return []

        patterns = [r.question_pattern for r in rows]
        # Use the provided cutoff so callers can control strictness.
        close = difflib.get_close_matches(query, patterns, n=top_k, cutoff=cutoff)
        results = []
        for match in close:
            for r in rows:
                if r.question_pattern == match:
                    score = difflib.SequenceMatcher(None, query, r.question_pattern).ratio()
                    results.append({
                        "id": r.id,
                        "question_pattern": r.question_pattern,
                        "answer": r.answer,
                        "source": r.source,
                        "score": round(score, 3),
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

# -------------------------
# Token endpoint (unchanged)
# -------------------------
@app.post("/token")
def token(identity: str, room: Optional[str] = None):
    try:
        t = generate_join_token(identity=identity, room=room)
        return {"token": t, "livekit_url": os.getenv("LIVEKIT_URL")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# Create help request (but first check KB)
# -------------------------
@app.post("/help-requests", response_model=dict)
def create_help_request(payload: CreateHelpRequest, kb_cutoff: float = 0.55, kb_search_cutoff: float = 0.35):
    """
    Called by the agent when handling a customer query.
    First check KB (fuzzy) using kb_search_cutoff to filter irrelevant patterns.
    If best match score >= kb_cutoff: return kb match and do NOT create request.
    Otherwise create a pending HelpRequest and return its id.
    """
    # 1) Check KB for possible answer — use a modest cutoff to avoid too-loose matches
    suggestions = find_kb_matches(payload.question, top_k=3, cutoff=kb_search_cutoff)
    best = suggestions[0] if suggestions else None

    if best and best["score"] >= kb_cutoff:
        # Confident KB answer — don't escalate
        return {
            "created": False,
            "kb_match": best,
            "message": "Knowledge base match found; agent can reply directly."
        }

    # Create pending help request (no confident KB match)
    with get_session() as session:
        req = HelpRequest(
            caller_name=payload.caller_name,
            question=payload.question,
            status="pending",
            livekit_room=payload.livekit_room
        )
        session.add(req)
        session.commit()
        session.refresh(req)

        # Also include any lower-confidence KB suggestion if present (useful)
        kb_suggestion = best if best else None

        return {"created": True, "id": req.id, "status": req.status, "message": "Supervisor notified (simulated).", "kb_suggestion": kb_suggestion}

# -------------------------
# List help requests
# -------------------------
@app.get("/help-requests", response_model=List[dict])
def list_help_requests(status: Optional[str] = None):
    with get_session() as session:
        q = select(HelpRequest)
        if status:
            q = q.where(HelpRequest.status == status)
        rows = session.exec(q).all()
        result = []
        for r in rows:
            result.append({
                "id": r.id,
                "caller_name": r.caller_name,
                "question": r.question,
                "status": r.status,
                "supervisor_response": r.supervisor_response,
                "created_at": r.created_at.isoformat(),
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                "livekit_room": r.livekit_room,
                "follow_up_sent": r.follow_up_sent,
            })
        return result

# -------------------------
# Supervisor responds -> updates request and optionally saves to KB
# -------------------------
@app.post("/help-requests/{req_id}/respond")
def respond_help_request(req_id: int, answer: SupervisorAnswer):
    with get_session() as session:
        req = session.get(HelpRequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")

        req.supervisor_response = answer.supervisor_response
        req.status = answer.status
        req.resolved_at = datetime.utcnow()
        req.follow_up_sent = False
        session.add(req)
        session.commit()
        session.refresh(req)

        # Policy: save to KB automatically when marked resolved OR if save_to_kb flag provided
        if answer.save_to_kb or (answer.status == "resolved"):
            kb = KnowledgeBase(
                question_pattern=req.question,
                answer=answer.supervisor_response,
                source="SUPERVISOR"
            )
            session.add(kb)
            session.commit()
            session.refresh(kb)

        return {"message": "Response recorded", "id": req.id}

# -------------------------
# Agent follow-up simulation
# -------------------------
@app.post("/help-requests/{req_id}/agent-followup")
def agent_followup(req_id: int):
    with get_session() as session:
        req = session.get(HelpRequest, req_id)
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
        if not req.supervisor_response:
            raise HTTPException(status_code=400, detail="No supervisor response to follow up with")

        req.follow_up_sent = True
        session.add(req)
        session.commit()
        session.refresh(req)

        follow_up_content = f"Hi {req.caller_name}, following up: {req.supervisor_response}"
        return {"follow_up": follow_up_content}

# -------------------------
# Knowledge Base endpoints
# -------------------------
@app.get("/learned-answers", response_model=List[dict])
def list_learned_answers():
    with get_session() as session:
        rows = session.exec(select(KnowledgeBase)).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "question_pattern": r.question_pattern,
                "answer": r.answer,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "source": r.source
            })
        return out

@app.post("/learned-answers", response_model=dict)
def create_learned_answer(payload: KBCreate):
    with get_session() as session:
        kb = KnowledgeBase(
            question_pattern=payload.question_pattern,
            answer=payload.answer,
            source=payload.source
        )
        session.add(kb)
        session.commit()
        session.refresh(kb)
        return {"id": kb.id, "message": "KB entry created"}

@app.get("/kb/search", response_model=List[dict])
def kb_search(q: str = Query(..., description="Query string to search KB"), top_k: int = 3, cutoff: float = 0.0):
    results = find_kb_matches(q, top_k=top_k, cutoff=cutoff)
    return results







# """ # backend/main.py
# from fastapi import FastAPI, HTTPException, Query
# from pydantic import BaseModel
# from typing import List, Optional
# from sqlmodel import select
# from dotenv import load_dotenv
# import os
# from datetime import datetime
# import difflib

# from .db import init_db, get_session
# from .models import HelpRequest, KnowledgeBase
# from .livekit_token import generate_join_token

# load_dotenv()

# app = FastAPI(title="FrontDesk Human-in-loop Backend")
# init_db()

# # -------------------------
# # Pydantic payload models
# # -------------------------
# class CreateHelpRequest(BaseModel):
#     caller_name: str
#     question: str
#     livekit_room: Optional[str] = None

# class SupervisorAnswer(BaseModel):
#     supervisor_response: str
#     status: str  # "resolved" or "unresolved"
#     save_to_kb: Optional[bool] = False  # optional flag to save into KB explicitly

# class KBCreate(BaseModel):
#     question_pattern: str
#     answer: str
#     source: Optional[str] = "MANUAL"

# # -------------------------
# # Helper: KB fuzzy search
# # -------------------------
# def find_kb_matches(query: str, top_k: int = 3, cutoff: float = 0.45):
#     Very simple fuzzy match using difflib against stored question_pattern values.
#     Returns a list of dictionaries: {id, question_pattern, answer, score}

#     with get_session() as session:
#         rows = session.exec(select(KnowledgeBase)).all()
#         # build list of (pattern, obj)
#         patterns = [r.question_pattern for r in rows]
#         # use difflib.get_close_matches to get near textual matches
#         close = difflib.get_close_matches(query, patterns, n=top_k, cutoff=cutoff)
#         results = []
#         for match in close:
#             # find the row object(s) with this pattern
#             for r in rows:
#                 if r.question_pattern == match:
#                     # compute a simple ratio score via SequenceMatcher
#                     score = difflib.SequenceMatcher(None, query, r.question_pattern).ratio()
#                     results.append({
#                         "id": r.id,
#                         "question_pattern": r.question_pattern,
#                         "answer": r.answer,
#                         "source": getattr(r, "source", None),
#                         "score": round(score, 3),
#                         "created_at": r.created_at.isoformat() if r.created_at else None
#                     })
#     # sort by score desc
#     results.sort(key=lambda x: x["score"], reverse=True)
#     return results

# # -------------------------
# # Token endpoint (unchanged)
# # -------------------------
# @app.post("/token")
# def token(identity: str, room: Optional[str] = None):
#     try:
#         t = generate_join_token(identity=identity, room=room)
#         return {"token": t, "livekit_url": os.getenv("wss://aiagent-vpq4w370.livekit.cloud")}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # -------------------------
# # Help requests endpoints (create/list/respond)
# # -------------------------
# @app.post("/help-requests", response_model=dict)
# def create_help_request(payload: CreateHelpRequest):
#     with get_session() as session:
#         req = HelpRequest(
#             caller_name=payload.caller_name,
#             question=payload.question,
#             status="pending",
#             livekit_room=payload.livekit_room
#         )
#         session.add(req)
#         session.commit()
#         session.refresh(req)

#         # Optionally check KB immediately to return a suggested answer to caller (agent can use it)
#         suggestions = find_kb_matches(payload.question, top_k=1, cutoff=0.4)
#         suggestion = suggestions[0] if suggestions else None

#         return {
#             "id": req.id,
#             "status": req.status,
#             "message": "Supervisor notified (simulated).",
#             "kb_suggestion": suggestion
#         }

# @app.get("/help-requests", response_model=List[dict])
# def list_help_requests(status: Optional[str] = None):
#     with get_session() as session:
#         q = select(HelpRequest)
#         if status:
#             q = q.where(HelpRequest.status == status)
#         rows = session.exec(q).all()
#         result = []
#         for r in rows:
#             result.append({
#                 "id": r.id,
#                 "caller_name": r.caller_name,
#                 "question": r.question,
#                 "status": r.status,
#                 "supervisor_response": r.supervisor_response,
#                 "created_at": r.created_at.isoformat(),
#                 "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
#                 "livekit_room": r.livekit_room,
#                 "follow_up_sent": r.follow_up_sent,
#             })
#         return result

# @app.post("/help-requests/{req_id}/respond")
# def respond_help_request(req_id: int, answer: SupervisorAnswer):
#     with get_session() as session:
#         req = session.get(HelpRequest, req_id)
#         if not req:
#             raise HTTPException(status_code=404, detail="Request not found")
#         req.supervisor_response = answer.supervisor_response
#         req.status = answer.status
#         req.resolved_at = datetime.utcnow()
#         req.follow_up_sent = False
#         session.add(req)
#         session.commit()
#         session.refresh(req)

#         # Save into KB if requested OR if request was resolved (simple policy)
#         if answer.save_to_kb or (answer.status == "resolved"):
#             kb = KnowledgeBase(
#                 question_pattern=req.question,
#                 answer=answer.supervisor_response,
#                 source="SUPERVISOR"
#             )
#             session.add(kb)
#             session.commit()
#             session.refresh(kb)

#         return {"message": "Response recorded", "id": req.id}
    



   
# # Knowledge Base endpoints

# @app.get("/learned-answers", response_model=List[dict])
# def list_learned_answers():
#     with get_session() as session:
#         rows = session.exec(select(KnowledgeBase)).all()
#         out = []
#         for r in rows:
#             out.append({
#                 "id": r.id,
#                 "question_pattern": r.question_pattern,
#                 "answer": r.answer,
#                 "created_at": r.created_at.isoformat() if r.created_at else None,
#                 "updated_at": r.updated_at.isoformat() if r.updated_at else None,
#                 "source": r.source
#             })
#         return out

# @app.post("/learned-answers", response_model=dict)
# def create_learned_answer(payload: KBCreate):
#     with get_session() as session:
#         kb = KnowledgeBase(
#             question_pattern=payload.question_pattern,
#             answer=payload.answer,
#             source=payload.source
#         )
#         session.add(kb)
#         session.commit()
#         session.refresh(kb)
#         return {"id": kb.id, "message": "KB entry created"}

# @app.get("/kb/search", response_model=List[dict])
# def kb_search(q: str = Query(..., description="Query string to search KB"), top_k: int = 3):
#     results = find_kb_matches(q, top_k=top_k, cutoff=0.4)
#     return results

#  """