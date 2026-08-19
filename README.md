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

# Create the tables (one-time)
psql -U postgres -d chhaya -f sql/schema.sql

# Run FastAPI Dev Server
uvicorn app.main:app --reload --port 8000
```

The Code Studio practice bank fills itself on first startup -- the server
notices the table is empty and imports a public LeetCode dataset from Kaggle
in the background, so the API is usable while it runs. That needs a Kaggle API
token of your own (kaggle.com -> Settings -> API -> Create New Token, saved to
`~/.kaggle/kaggle.json`); without one the server logs how to fix it and starts
normally with an empty Practice tab. See `PRACTICE_DATASET_SLUG` in
`.env.example` to change datasets or turn the automatic import off.

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
