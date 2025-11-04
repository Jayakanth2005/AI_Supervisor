# Use an official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install dependencies (combine both UI + backend if you want one container)
RUN pip install --no-cache-dir -r supervisor_ui/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# (Optional) Install extra voice libs
RUN apt-get update && apt-get install -y \
    espeak ffmpeg libespeak1 && \
    rm -rf /var/lib/apt/lists/*

# Expose Streamlit and FastAPI ports
EXPOSE 8501
EXPOSE 8000

# Default command runs Streamlit app
CMD ["streamlit", "run", "supervisor_ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
