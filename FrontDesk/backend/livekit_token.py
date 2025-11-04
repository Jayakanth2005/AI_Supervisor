
# backend/livekit_token.py
import os
import time
import jwt  # pyjwt
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://aiagent-vpq4w370.livekit.cloud")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "APIZEQka6PvBsVE")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "ui9rVdsLhFzSaVJeAa1hYuxuEVDDVSpffWcDQSezDdWC")

# LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://aiagent-vpq4w370.livekit.cloud")
#  API_KEY = os.getenv("LIVEKIT_API_KEY", "APIZEQka6PvBsVE")
#  API_SECRET = os.getenv("LIVEKIT_API_SECRET", "ui9rVdsLhFzSaVJeAa1hYuxuEVDDVSpffWcDQSezDdWC")

def generate_join_token(identity: str, room: Optional[str] = None, ttl_seconds: int = 60*60):
    """
    Generate a LiveKit join token (JWT). identity is the client identity (username).
    room optional restricts token to a specific room.
    """
    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise RuntimeError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment")

    now = int(time.time())
    payload = {
        "jti": f"{identity}-{now}",
        "iss": LIVEKIT_API_KEY,
        "nbf": now - 5,
        "exp": now + ttl_seconds,
        "sub": identity,
        "grants": {
            "room": room or "*"
        }
    }
    token = jwt.encode(payload, LIVEKIT_API_SECRET, algorithm="HS256")
    # pyjwt returns str on v2; ensure string
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token
