# Use official Python image
FROM python:3.10-slim

WORKDIR /app
COPY . .

# Install all system dependencies required for audio, speech & TTS
RUN apt-get update && apt-get install -y \
    espeak ffmpeg libespeak1 \
    portaudio19-dev python3-pyaudio build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r supervisor_ui/requirements.txt

# Expose backend and frontend ports
EXPOSE 8000
EXPOSE 8501

# Default command: start Streamlit UI
CMD ["streamlit", "run", "supervisor_ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
