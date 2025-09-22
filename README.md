# FinCompliance — AI‑powered RBI Compliance Assistant

FinCompliance helps compliance teams monitor RBI regulatory updates and turn official documents into actionable answers. It continuously collects RBI Master Circulars and Press Releases, lets you pull any PDF into a vector store, and enables grounded, document‑centric chat and workflow‑based analysis.

The assistant is designed to be precise, conservative, and explicitly grounded in retrieved RBI content.

## Features

- RBI updates scraping to Postgres (Neon) for Press Releases and Master Circulars
- Pull & Chat with any RBI PDF (pdfplumber → chunking → embeddings → Pinecone)
- Grounded Q&A via a ReAct‑style agent over retrieved document context (no speculation)
- Workflows for multi‑document analysis and persistent, per‑workflow chat history
- General chat history and persistence
- Optional Slack notifications for new items or system events
- Frontend authentication with Clerk

## Tech

- Frontend: Vite, React, Chakra UI, Clerk
- Backend: FastAPI, Uvicorn, LangChain, LangGraph, pdfplumber
- Vector/ML: Pinecone, sentence‑transformers (all‑mpnet‑base‑v2), OpenRouter + ChatOpenAI
- Database: Postgres (Neon)

## Run Locally

Prerequisites:
- Python 3.10+
- Node.js 18+
- pip
- Postgres database (e.g., Neon)
- Pinecone account + API key
- OpenRouter API key
- (Optional) Slack Incoming Webhook URL
- (Optional) Clerk Publishable Key for the frontend

1) Backend (API)

```bash
cd api
# 1. Environment
copy .env.example .env   # On Windows (PowerShell/CMD)
# or: cp .env.example .env  # On macOS/Linux

# 2. Install
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
# On macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# 3. Run (development)
# Ensure in .env: ENVIRONMENT=development and (optionally) PORT=5000
python app.py
# or equivalently
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

The API will start on http://localhost:5000 by default (unless you override PORT).

2) Frontend (Client)

```bash
cd client
# 1. Environment
copy .env.example .env   # On Windows (PowerShell/CMD)
# or: cp .env.example .env  # On macOS/Linux

# 2. Install & run
npm install
npm run dev
```

Open the app at http://localhost:5173 and set `VITE_API_URL` to point at your API (e.g., http://localhost:5000).

## Environment Variables

Backend (`api/.env`):
- OPEN_ROUTER_API_KEY — OpenRouter API key
- PINECONE_API_KEY — Pinecone API key
- PGHOST — Postgres host (Neon)
- PGDATABASE — Postgres database name
- PGUSER — Postgres user
- PGPASSWORD — Postgres password
- PGSSLMODE — SSL mode (default: `require`)
- PGCHANNELBINDING — Channel binding mode if required by your provider
- SLACK_WEBHOOK_URL — Slack webhook URL (optional)
- HOST — Bind host (default: `0.0.0.0`)
- PORT — API port (default: `5000` locally; `10000` on Render as configured)
- ENVIRONMENT — `development` or `production`

Frontend (`client/.env`):
- VITE_CLERK_PUBLISHABLE_KEY — Clerk publishable key
- VITE_API_URL — Base URL of the API (e.g., http://localhost:5000)
- VITE_SLACK_INVITE_URL — Public invite link to your Slack (optional)

Never commit `.env` files to version control.

## Acknowledge

This project was developed during Symbiot Hackathon 2025.
