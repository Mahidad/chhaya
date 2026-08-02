# Chhaya – A Personalized Teaching Style Learning Platform

Chhaya is a modular AI-assisted study and learning application.

## Repository Structure

- [chhaya-backend](./chhaya-backend): FastAPI backend service structured in clean domain layers (`api`, `schemas`, `services`, `repositories`, `models`, `core`).
- [chhaya-frontend](./chhaya-frontend): React + Vite frontend user interface built with clean custom CSS and responsive design components.
- [logo-assets](./logo-assets): Jar logo vector assets and transparent PNGs (`logo-black-transparent.png`, `logo-white-transparent.png`).

---

## Quick Start Guide

### 1. Prerequisites

- Python 3.10+
- Node.js 18+ & npm

### 2. Backend Setup

```bash
cd chhaya-backend
python -m venv venv
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # Generate or update JWT_SECRET_KEY in .env

# Run FastAPI Dev Server
uvicorn app.main:app --reload --port 8000
```

FastAPI Interactive API documentation will be available at:
`http://localhost:8000/docs`

### 3. Frontend Setup

```bash
cd chhaya-frontend
npm install
cp .env.example .env   # Points to VITE_API_BASE_URL=http://localhost:8000/api/v1

# Run Development Server
npm run dev
```

Frontend application will be accessible at:
`http://localhost:5173`

---

## License

All rights reserved.
