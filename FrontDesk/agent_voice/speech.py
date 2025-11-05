import os
import tempfile
import threading
from gtts import gTTS
import pygame

_tts_lock = threading.Lock()

def speak(text: str):
    """Use gTTS to generate and play speech (works inside Docker)."""
    if not text or not text.strip():
        return

    def _worker():
        with _tts_lock:
            try:
                # Generate speech as temporary MP3 file
                tts = gTTS(text=text, lang='en')
                tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(tmpfile.name)
                tmpfile.close()

                # Initialize pygame mixer for playback
                pygame.mixer.init()
                pygame.mixer.music.load(tmpfile.name)
                pygame.mixer.music.play()

                # Wait until playback is done
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                # Cleanup
                pygame.mixer.music.unload()
                os.remove(tmpfile.name)
                pygame.mixer.quit()
            except Exception as e:
                print(f"[TTS Error] {e}")

    threading.Thread(target=_worker, daemon=True).start()
