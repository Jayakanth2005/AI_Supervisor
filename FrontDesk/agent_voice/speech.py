import speech_recognition as sr
import pyttsx3
import threading

# Initialize recognizer and TTS engine once
recognizer = sr.Recognizer()
tts_engine = pyttsx3.init()

# Lock for safe concurrent access
_engine_lock = threading.Lock()

def listen():
    """Listen to microphone and return recognized text."""
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"🗣 You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return ""
        except sr.RequestError:
            print("API unavailable.")
            return ""

def speak(text):
    """Thread-safe TTS function to avoid 'run loop already started' errors."""
    def _do_speak():
        try:
            with _engine_lock:
                tts_engine.say(text)
                tts_engine.runAndWait()
        except RuntimeError:
            # Handle overlapping TTS run loops safely
            try:
                tts_engine.stop()
                tts_engine.say(text)
                tts_engine.runAndWait()
            except Exception as e:
                print(f"[WARN] Speech engine error: {e}")

    # Run TTS in a separate thread to avoid Streamlit re-run issues
    threading.Thread(target=_do_speak, daemon=True).start()
