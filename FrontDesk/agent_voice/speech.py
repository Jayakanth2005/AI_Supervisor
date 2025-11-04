# agent_voice/speech.py
import pyttsx3
import threading
import time
import re

_tts_lock = threading.Lock()

def _init_engine():
    """Always reinitialize engine per call — stable in Streamlit."""
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    for v in voices:
        if "female" in v.name.lower():
            engine.setProperty("voice", v.id)
            break
    engine.setProperty("rate", 175)
    return engine

def _chunk_text(text: str, max_chars: int = 250):
    """Break long text into smaller chunks for smoother playback."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + " " + s).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks

def speak(text: str):
    """Speak text each time freshly — works across Streamlit reruns."""
    if not text or not text.strip():
        return

    def _worker():
        try:
            engine = _init_engine()
            chunks = _chunk_text(text)
            with _tts_lock:
                for chunk in chunks:
                    engine.say(chunk)
                    engine.runAndWait()
                    time.sleep(0.05)
            engine.stop()
        except Exception as e:
            print(f"[TTS Error] {e}")

    threading.Thread(target=_worker, daemon=True).start()
