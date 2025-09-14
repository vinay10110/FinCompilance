# FinCompliance — AI‑powered RBI Compliance Assistant

Live demo: https://fin-compilance.vercel.app/

FinCompliance helps compliance teams monitor RBI regulatory updates and turn official documents into actionable answers. It continuously collects RBI Master Circulars and Press Releases, lets you pull any PDF into a vector store, and enables grounded, document-centric chat and workflow-based analysis.

The assistant is designed to be precise, conservative, and explicitly grounded in the retrieved RBI content.


## Why this exists

- Rapidly growing RBI update surface (press releases, master circulars) is hard to track manually.
- Compliance analysts need fast, accurate answers grounded in official text, not guesswork.
- Teams want repeatable “workflows” around specific topics/documents and persistent discussion context.


## High-level architecture

```
monorepo
├─ api/                 # FastAPI backend
│  ├─ app.py            # HTTP API & startup scraping
│  ├─ press_scrapper.py # RBI press releases scraper
│  ├─ circulars_scrapper.py # RBI master circulars scraper
│  ├─ vectorizer.py     # PDF → text → embeddings → Pinecone
│  ├─ llm.py            # ReAct agent over Pinecone (OpenRouter + LangChain)
│  ├─ workflow_agent.py # Workflow Q&A agent using multiple documents
│  ├─ neon_database.py  # Neon/Postgres data access functions
│  └─ notifications.py  # Slack webhook notifications
└─ client/              # Vite + React + Chakra UI frontend
   └─ src/
      ├─ components/    # Chat, Sidebar (documents), Workflows UI
      ├─ pages/         # Workflows page
      └─ App.jsx        # Routing, Clerk auth wrappers
```

Key services and data stores:
- Postgres (Neon): authoritative store for press releases, circulars, chat history, workflows.
- Pinecone: vector store for chunked PDF content per document namespace.
- OpenRouter + ChatOpenAI (via LangChain): LLM that reasons over retrieved context with a ReAct-style agent.


## What the product does

- RBI updates at a glance
  - The backend scrapes official pages and stores normalized records in Postgres:
    - Press Releases: `api/press_scrapper.py`
    - Master Circulars: `api/circulars_scrapper.py`
  - Frontend sidebar presents “Today” vs “Previous” updates (and circular categories).

- Pull & Chat with any RBI PDF
  - Select a press release/circular and click “Pull & Chat”.
  - Backend downloads the PDF, extracts text with `pdfplumber`, chunks with `RecursiveCharacterTextSplitter`, embeds using `sentence-transformers/all-mpnet-base-v2`, and upserts to Pinecone under a document-specific namespace:
    - Code: `api/vectorizer.py` → `process_and_store_pdf()`
    - Pinecone index: `fincompilance`
    - Namespace: `pdf_chunks_{doc_id}`

- Grounded Q&A on top of the PDF
  - When you ask a question, the ReAct agent retrieves top-k relevant chunks from the document’s namespace and answers strictly from that context.
  - Code: `api/llm.py` → `pinecone_query_tool()` + `get_agent_executor()` + `ask_doc_question()`
  - The system prompt explicitly forbids speculation and reminds that it’s not legal advice.

- Workflows for multi-document analysis
  - Create a workflow, add multiple documents (press releases and/or circulars), and chat in the context of that curated set.
  - The workflow agent can choose relevant document namespaces based on titles and answer accordingly.
  - Code: `api/workflow_agent.py` and related API routes in `api/app.py`.

- Persistence & history
  - General chat history: `chat_messages` table, surfaced by `/getchats`.
  - Workflow chat history with per-message metadata (including optional document payloads): `workflow_chat_messages`.

- Notifications (optional)
  - Slack webhook notifications are available for new items and system messages: `api/notifications.py`.


## How it works (end‑to‑end flows)

1) Startup data ingestion
- `api/app.py` runs a one-time scrape on application start (`@app.on_event("startup")`).
- New entries are normalized, deduplicated, and saved into Postgres:
  - Press releases: `press_releases` table (normalized URL, optional PDF URL, dates, `doc_id` hash).
  - Master circulars: `rbi_circulars` table (category, normalized PDF URL, dates, `doc_id`).

2) Pull & Chat (single-document)
- User picks a document in the UI sidebar (`client/src/components/Sidebar.jsx`).
- Frontend calls `POST /vectorize` with `pdf_link` and `doc_id`.
- Backend (`vectorizer.py`) downloads the PDF, extracts text+tables, chunks, embeds, and upserts to Pinecone namespace `pdf_chunks_{doc_id}`.
- Chat requests go to `POST /process_message` with the `doc_id`, which invokes the ReAct agent (`llm.py`) to retrieve and answer from that exact namespace.

3) Workflows (multi-document)
- Create: `POST /workflows`.
- Add document: `POST /workflows/{workflow_id}/documents` (automatically vectorizes if needed and associates the DB record to the workflow).
- Chat: `POST /workflows/{workflow_id}/chat` uses a workflow agent to pick relevant namespaces (`workflow_agent.py`).
- History: `GET /workflows/{workflow_id}/chat/history` returns persistent, ordered messages.


## API overview (selected)

- GET `/get_updates` — Latest RBI press release entries from Postgres.
- GET `/get_circulars` — Latest Master Circulars with categories.
- POST `/vectorize` — Vectorize a PDF into Pinecone (`doc_id`, `pdf_link`).
- POST `/process_message` — Grounded Q&A over a single `doc_id`.
- POST `/save_message` — Persist a general chat message.

Workflows:
- POST `/workflows` — Create an empty workflow.
- GET `/workflows?user_id=...` — List workflows for a user.
- GET `/workflows/{workflow_id}` — Workflow details + linked documents.
- POST `/workflows/{workflow_id}/documents` — Add a document to a workflow (includes vectorization).
- POST `/workflows/{workflow_id}/chat?user_id=...` — Q&A over the workflow’s documents.
- GET `/workflows/{workflow_id}/chat/history?user_id=...` — Retrieve workflow chat history.
- POST `/workflows/{workflow_id}/chat/save` — Save a workflow chat message manually.
- DELETE `/workflows/{workflow_id}/chat/clear` — Clear workflow chat history.
- DELETE `/workflows/{workflow_id}/documents` — Remove a document from a workflow.
- DELETE `/workflows/{workflow_id}` — Delete a workflow.

See `api/app.py` for exact request/response shapes.


## Core implementation details

- LLM & Retrieval
  - `ChatOpenAI` via OpenRouter, model `openai/gpt-3.5-turbo` (see `api/llm.py`).
  - ReAct-style agent (`langgraph.prebuilt.create_react_agent`) with a custom `pinecone_query` tool.
  - Strict grounding: the system prompt instructs the model to answer only from retrieved RBI context and to acknowledge when context is insufficient.

- Embeddings & Vector store
  - Embeddings: `SentenceTransformer('all-mpnet-base-v2')` (see `api/vectorizer.py`, `api/llm.py`, `api/workflow_agent.py`).
  - Vector DB: Pinecone index `fincompilance`, namespaces as `pdf_chunks_{doc_id}`.
  - PDF parsing: `pdfplumber` with both text and table extraction; tables are serialized into chunk content.

- Scrapers (reliable, polite)
  - `requests` + `BeautifulSoup` with retry/backoff and a proper `User-Agent`.
  - Deduping via normalized links and SHA-256 `doc_id` hashes.
  - Files: `api/press_scrapper.py`, `api/circulars_scrapper.py`.

- Persistence (Neon/Postgres)
  - Data access layer in `api/neon_database.py`.
  - Tables leveraged by the app include: `press_releases`, `rbi_circulars`, `chat_messages`, `workflows`, `workflow_documents`, `workflow_chat_messages`.

- Frontend UX (Vite + React + Chakra UI)
  - `client/src/components/Sidebar.jsx`: RBI updates browser (filtering, categories, today vs previous) and document actions.
  - `client/src/components/ChatInterface.jsx`: single-document “Pull & Chat” experience.
  - `client/src/pages/WorkflowsPage.jsx` + `components/WorkflowChatInterface.jsx`: create workflows, add documents, multi-document chat, persistent history.
  - Authentication with Clerk (`App.jsx`), optional “Join Slack” CTA.

- Operational characteristics
  - One-time scraping runs on app startup (`@app.on_event("startup")` in `api/app.py`).
  - Production startup script (`api/start_production.py`) optimizes for low memory (no reload, single worker, lower log verbosity). 
  - All heavy models/clients (OpenRouter LLM, Pinecone, SentenceTransformer) are lazy-loaded and cached in-process to reduce cold-start memory.

## Tech stack

- Frontend: Vite, React, Chakra UI, Clerk (auth)
- Backend: FastAPI, Psycopg2, LangChain, LangGraph, pdfplumber
- Vector/ML: Pinecone, sentence-transformers (all-mpnet-base-v2), OpenRouter + ChatOpenAI
- Database: Postgres (Neon)
- Notifications: Slack webhook (optional)
