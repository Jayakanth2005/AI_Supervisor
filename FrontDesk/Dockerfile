# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy entire project into container
COPY . .

# Install system dependencies (needed for TTS + audio)
RUN apt-get update && apt-get install -y \
    espeak ffmpeg libespeak1 portaudio19-dev python3-pyaudio build-essential && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install Python dependencies (for both backend & frontend)
RUN pip install --no-cache-dir -r supervisor_ui/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose both ports
EXPOSE 8000
EXPOSE 8501

# Default command: run Streamlit app
CMD ["streamlit", "run", "supervisor_ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
