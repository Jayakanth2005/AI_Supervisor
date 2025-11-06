# 🧠 AI Supervisor

An intelligent, voice-enabled assistant system powered by **FastAPI**, **Streamlit**, and **Speech Recognition** — designed to handle real-time customer interactions, analyze knowledge base queries, and escalate unresolved cases to a human supervisor.  

This project integrates **speech-to-text**, **text-to-speech**, and **AI-driven knowledge responses** within a clean, modular architecture.

---

## 🚀 Features

- 🎙 **Voice Input** – Convert speech to text using Google Speech Recognition  
- 🔊 **Voice Output** – Respond to users via gTTS (Google Text-to-Speech)  
- ⚙️ **FastAPI Backend** – Lightweight, async Python backend  
- 🖥 **Streamlit Frontend** – Interactive, browser-based UI  
- 🧩 **Modular Structure** – Separate `agent_voice`, `backend`, and `frontend`  
- 🐳 **Docker Ready** – Fully containerized with `docker-compose`  
- 🔐 **Environment Variables** – Easy configuration for backend URLs and IDs  
- 🧠 **Knowledge Base Support** – Smart response with fallback to supervisor escalation  

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|-------------|
| Frontend | Streamlit |
| Backend | FastAPI |
| Voice Processing | SpeechRecognition, gTTS, pygame |
| Language | Python 3.10+ |
| Deployment | Docker + Docker Compose |
| Audio Format | WAV (16kHz, mono) |

---

## 📋 Prerequisites

### For Docker Setup (Recommended)
- Docker 20.0+  
- Docker Compose 2.0+

### For Local Development
- Python 3.10 or above  
- pip (latest version)  
- Microphone and speaker access  

---

## 🚀 Quick Start

### Option 1:  Local Setup (Recommended)

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Jayakanth2005/AI_Supervisor.git
   cd AI_Supervisor
   ```
   
2. **Backend Setup**
   
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate   # On Windows
   # source venv/bin/activate  (Linux/Mac)
   pip install -r requirements.txt
   uvicorn main:app --reload

   Backend runs at http://127.0.0.1:8000
   ```

3. **Frontend Setup**

   ```bash
   cd ../supervisor_ui
   pip install -r requirements.txt
   streamlit run app.py

   Frontend run in http://localhost:8501
   ```

### Option 2: Docker Setup

   **Docker Building and running**
   ```bash
   docker-compose up --build
   docker-compose run
   ```


   
