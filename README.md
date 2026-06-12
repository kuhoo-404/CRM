# SenAI CRM — AI-Powered Email Triage System

> Autonomous CRM intelligence platform with RAG pipeline, ReAct agent, and real-time dashboard.  


---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Variables](#environment-variables)
3. [How to Seed the Knowledge Base](#how-to-seed-the-knowledge-base)
4. [How to Run the Email Simulation](#how-to-run-the-email-simulation)
5. [Architecture Overview](#architecture-overview)
6. [Architecture Decisions & Trade-offs](#architecture-decisions--trade-offs)
7. [Known Limitations](#known-limitations)
8. [API Reference](#api-reference)

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 17
- A Groq API key (free tier works — [console.groq.com](https://console.groq.com))

### 1. Clone and set up backend

```bash
git clone https://github.com/YOUR_USERNAME/senai-crm.git
cd senai-crm

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `backend/.env` and fill in your values:

```bash
cp .env.example backend/.env
```

### 3. Create database and run migrations

```bash
# Create the PostgreSQL database
psql -U postgres -c "CREATE DATABASE senai_crm;"

# Run migrations
cd backend
alembic upgrade head
```

### 4. Seed the knowledge base (RAG)

```bash
cd backend
python scripts/seed_kb.py
```

This chunks and embeds all 6 knowledge base documents into ChromaDB (~90MB model download on first run).

### 5. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 6. Seed email data

```bash
curl -X POST http://localhost:8000/api/seed
```

Or via PowerShell:
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/seed" -Method POST -UseBasicParsing
```

### 7. Classify all emails

```bash
python -c "
from app.database import SessionLocal
from app.models.email import Email, EmailStatus
from app.services.classifier_service import classify_email
import time

db = SessionLocal()
unclassified = db.query(Email).filter(
    Email.category == None,
    Email.is_spam == False,
    Email.is_internal == False,
).all()
print(f'Classifying {len(unclassified)} emails...')
for e in unclassified:
    try:
        classify_email(e.id, db)
        print(f'OK: {e.message_id}')
        time.sleep(2)
    except Exception as ex:
        print(f'SKIP: {e.message_id} — {ex}')
db.close()
print('Done')
"
```

### 8. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: **http://localhost:5173**

---

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/senai_crm` |
| `GROQ_API_KEY` | Groq API key for LLM calls | `gsk_...` |
| `GEMINI_API_KEY` | Google Gemini API key (optional fallback) | `AIza...` |
| `ANTHROPIC_API_KEY` | Anthropic API key (optional fallback) | `sk-ant-...` |
| `APP_ENV` | Environment (`development` / `production`) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path | `./chroma_db` |
| `KB_DIR` | Knowledge base documents directory | `./knowledge_base` |
| `CHUNK_SIZE` | RAG chunk size in tokens | `400` |
| `CHUNK_OVERLAP` | Overlap between chunks | `50` |
| `RAG_TOP_K` | Number of chunks to retrieve per query | `3` |
| `SCRAPER_CACHE_TTL` | Web scraper cache TTL in seconds | `21600` |

---

## How to Seed the Knowledge Base

The RAG pipeline requires the 6 knowledge base `.md` files to be chunked, embedded, and stored in ChromaDB before the classifier can run.

```bash
cd backend
python scripts/seed_kb.py
```

**What this does:**
1. Reads all `.md` files from `knowledge_base/`
2. Splits each document into 400-token chunks with 50-token overlap (26 chunks total)
3. Embeds each chunk using `all-MiniLM-L6-v2` (sentence-transformers, runs locally — no API key needed)
4. Upserts all vectors into ChromaDB at `./chroma_db`

**To verify the KB is seeded:**
```bash
curl "http://localhost:8000/rag/search?q=refund+policy"
```

Should return 3 chunks with similarity scores from `refund_policy.md`.

**To re-seed after updating KB documents:**
```bash
# Delete existing ChromaDB and re-run
rm -rf backend/chroma_db
python scripts/seed_kb.py
```

---

## How to Run the Email Simulation

### Option 1: Bulk seed (instant — loads all 60 emails at once)

```bash
curl -X POST http://localhost:8000/api/seed
```

Safe to run multiple times — duplicate `message_id` values are silently skipped (idempotent).

### Option 2: Stream simulation (realistic — one email at a time)

```bash
cd backend
python -c "
import json, time, requests
from pathlib import Path

emails = json.loads(Path('../data/email-data-advanced.json').read_text())
print(f'Streaming {len(emails)} emails at 1/sec...')
for email in emails:
    r = requests.post('http://localhost:8000/api/ingest', json=email)
    result = r.json()
    status = 'DUPLICATE' if result.get('data', {}).get('duplicate') else 'OK'
    print(f'{status}: {email[\"message_id\"]} — {email[\"subject\"][:50]}')
    time.sleep(1)
print('Stream complete.')
"
```

Adjust `time.sleep(1)` to control speed (e.g., `0.5` for faster simulation).

### Option 3: Single email ingest

```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"message_id": "test_001", "sender": "test@example.com", "subject": "Test", "body": "Hello"}'
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        EMAIL INGESTION                           │
│  POST /api/ingest → Schema Validation → Deduplication           │
│       → Heuristic Filter → Contact Upsert → Thread Link         │
│       → Persist to PostgreSQL → Audit Log                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   HEURISTIC FILTER      │
              │  (sub-10ms, no LLM)     │
              │  Spam / Security /      │
              │  Legal / Urgency        │
              └────────────┬────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │         LLM CLASSIFIER              │
         │  RAG Retrieval (ChromaDB)           │
         │  → top-3 policy chunks              │
         │  → Thread history                   │
         │  → Groq llama-3.3-70b              │
         │  → Structured JSON output           │
         │  → Save: category, sentiment,       │
         │    urgency, confidence              │
         └─────────────────┬──────────────────┘
                           │
         ┌─────────────────▼──────────────────┐
         │       AUTONOMOUS AGENT              │
         │  ReAct loop (max 6 steps)           │
         │  Tools: search_kb, get_thread,      │
         │  get_contact, check_account,        │
         │  draft_reply, escalate_to_human,    │
         │  flag_for_legal, create_ticket,     │
         │  send_auto_reply                    │
         │  → Reasoning trace stored in DB     │
         └─────────────────┬──────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │              POSTGRESQL                      │
    │  7 tables: contacts, threads, emails,        │
    │  actions, knowledge_chunks,                  │
    │  web_intelligence_cache, audit_log           │
    └──────────────────────┬──────────────────────┘
                           │
    ┌──────────────────────▼──────────────────────┐
    │           REACT FRONTEND                     │
    │  View 1: Mission Control Inbox               │
    │  View 2: Thread Workspace + Agent Trace      │
    │  View 3: Analytics Dashboard                 │
    └─────────────────────────────────────────────┘
```

---

## Architecture Decisions & Trade-offs

### LLM: Groq (llama-3.3-70b-versatile) over OpenAI/Gemini

**Decision:** Use Groq's free tier with `llama-3.3-70b-versatile` as the primary LLM.

**Why:** Groq offers significantly faster inference than OpenAI (typically <1s vs 3-5s) with a generous free tier that doesn't require a credit card. The `llama-3.3-70b` model produces structured JSON output reliably with low temperature settings.

**Trade-off:** Groq's free tier has rate limits (~30 req/min). In production, we would use a paid tier or implement a proper queue with retry logic. OpenAI GPT-4o would produce more consistent JSON output but costs ~$0.01 per classification.

**Alternative considered:** Gemini 2.0 Flash — rejected because `google.generativeai` SDK is deprecated and the new `google.genai` SDK had `%` character interpolation issues with Alembic config.

---

### Embedding Model: all-MiniLM-L6-v2 (local) over OpenAI Embeddings

**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2` running locally via the `sentence-transformers` library.

**Why:** Zero API cost, no rate limits, works offline, 90MB one-time download. For 26 chunks this is more than sufficient — similarity scores consistently above 0.60 for relevant queries.

**Trade-off:** Lower embedding quality than `text-embedding-ada-002` (OpenAI) or `embed-english-v3.0` (Cohere) for nuanced semantic queries. For a 26-chunk knowledge base this trade-off is acceptable. At scale (10,000+ chunks), a more powerful embedding model would improve retrieval precision.

**Alternative considered:** OpenAI `text-embedding-ada-002` — would cost ~$0.0001 per chunk (negligible) but adds an external API dependency for a component that runs locally with no quality loss at this scale.

---

### Vector Database: ChromaDB over Pinecone/pgvector

**Decision:** Use ChromaDB with local persistence.

**Why:** Zero setup, no account required, persists to disk, Python-native. For 26 chunks, ChromaDB returns top-3 results in <50ms consistently — well within the 200ms requirement.

**Trade-off:** ChromaDB is not horizontally scalable and is not suitable for production deployments with millions of vectors. At scale, we would migrate to pgvector (keeps everything in PostgreSQL, simplifies ops) or Pinecone (managed, scalable).

**Alternative considered:** pgvector — ideal for production because it eliminates a separate service. Rejected for this project because it requires a PostgreSQL extension and adds setup complexity for reviewers.

---

### Agent Pattern: ReAct over Function Calling

**Decision:** Implement ReAct (Reasoning + Acting) via structured JSON prompts rather than native function calling APIs.

**Why:** ReAct produces an explicit reasoning trace (`Thought → Action → Observation`) that is stored in the database and surfaced in the UI — exactly what the assignment requires. Native function calling (OpenAI tool_calls, Gemini function_declarations) abstracts the reasoning away from the response, making the trace harder to capture and display.

**Trade-off:** Structured JSON prompting is less reliable than native function calling — the LLM occasionally wraps output in markdown fences or produces malformed JSON. We mitigate this with a robust `_parse_response()` function that strips fences and extracts JSON substrings. A production system would use native function calling with a separate trace logger.

---

### Chunking Strategy: Fixed-size (400 tokens, 50 overlap) over Semantic Chunking

**Decision:** Split documents into fixed 400-token word-count chunks with 50-token overlap.

**Why:** Simple, fast, no additional models required. 400 tokens is large enough to include full policy paragraphs with context, and small enough to be precise in retrieval. The 50-token overlap ensures that policies spanning chunk boundaries are captured by at least one chunk.

**Trade-off:** Fixed-size chunking can split mid-sentence or mid-policy, reducing coherence. Semantic chunking (splitting at paragraph/section boundaries) would produce better chunks but requires either a custom parser per document or an additional NLP model. For 6 well-structured `.md` files, fixed-size chunking performs well enough — all test queries return scores above 0.55.

---

### Database: PostgreSQL over MongoDB/SQLite

**Decision:** PostgreSQL with SQLAlchemy ORM and Alembic migrations.

**Why:** The data is highly relational (emails → threads → contacts → actions). PostgreSQL handles JSON columns (for `raw_entities`, `agent_reasoning_log`, `diff`) natively via the `JSON` column type, giving us the best of both worlds. Alembic provides versioned, reversible migrations.

**Trade-off:** PostgreSQL requires local installation (more setup friction than SQLite). We mitigate this with clear setup instructions. SQLite was considered for development simplicity but rejected because it doesn't support the `JSON` column type natively in all SQLAlchemy versions, and switching databases between dev and production introduces risk.

---

### Frontend: React + Vite + Tailwind over Next.js

**Decision:** Bare React with Vite bundler and Tailwind CSS utility classes.

**Why:** Vite starts in <500ms (vs Next.js ~3s), has zero config for a pure frontend app, and Tailwind gives full design control without a component library dependency. For a dashboard that talks to a local API, server-side rendering (Next.js's main advantage) is unnecessary.

**Trade-off:** No SSR, no built-in routing optimizations. For this project (local development, demo), this is a non-issue. Recharts is used for data visualization — battle-tested, React-native, no canvas dependencies.

---

## Known Limitations

### 1. Web Intelligence Module (not implemented)
The assignment specifies scraping G2/Trustpilot for public sentiment when handling churn threats. This module is architecturally planned (the `web_intelligence_cache` table exists in the schema) but not implemented due to time constraints. The agent correctly identifies when web intelligence should be triggered (sentiment < -0.6, churn threat detected) but proceeds without the scraped data. In production, an async Playwright-based scraper with 6-hour caching would be added.

### 2. Groq Rate Limits on Free Tier
The free tier allows ~30 requests/minute. Bulk classification of 60 emails requires running the classifier script 3-4 times with 2-3 second delays between requests. A production system would use a task queue (Celery + Redis) with exponential backoff retry logic.

### 3. Account Data Not Populated
Contact profiles show `account_value: $0.00` and `churn_risk_score: 0.00` for all contacts because the seed data doesn't include billing information. The agent's `check_account_status` tool correctly infers subscription tier from account value, but with $0.00 baseline data, all contacts show as "Starter" tier. In production, this would be populated from a billing system (Stripe API).

### 4. WebSocket Not Implemented
The frontend polls every 10 seconds for updates. The assignment bonus requests WebSocket push notifications. The polling approach works correctly but has a maximum 10-second latency for new email visibility. A WebSocket implementation would use FastAPI's `websockets` support with a simple pub/sub pattern.

### 5. Email Simulation is HTTP-based, not SMTP
The system ingests emails via `POST /api/ingest` rather than connecting to a real email server. A production system would use IMAP polling or a webhook from a mail provider (SendGrid Inbound Parse, Gmail API, etc.). The current approach is correct for this assessment's dataset-based simulation.

### 6. No Authentication
All API endpoints are unauthenticated. A production system would implement JWT-based auth with role-based access control (support agents vs. managers vs. admins).

### 7. Docker Compose Not Implemented
The bonus Docker Compose deployment is not included. All services (PostgreSQL, ChromaDB, FastAPI, React) run locally. A production `docker-compose.yml` would containerize all four services with health checks and volume mounts.

---

## API Reference

Full OpenAPI specification available at: **http://localhost:8000/docs**

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/ingest` | Ingest a new email |
| GET | `/api/status/{job_id}` | Check processing status |
| POST | `/api/seed` | Seed all 60 emails from dataset |
| GET | `/dashboard/stats` | Inbox counts by status |
| GET | `/dashboard/category-breakdown` | Category distribution |
| GET | `/threads` | All threads with emails |
| GET | `/threads/{contact_email}` | Thread by contact |
| GET | `/threads/{contact_email}/history` | Full email history |
| POST | `/respond/{email_id}` | Send a reply |
| PATCH | `/drafts/{id}` | Edit a draft |
| POST | `/drafts/{id}/approve` | Approve and send |
| GET | `/contacts` | All contacts |
| GET | `/contacts/{email}` | Contact profile |
| PATCH | `/contacts/{email}/status` | Update status |
| GET | `/rag/search` | Debug: query knowledge base |
| POST | `/rag/classify/{email_id}` | Classify an email |
| GET | `/rag/analytics/sentiment-trend` | Sentiment trend data |
| POST | `/agent/run/{email_id}` | Run agent on email |
| POST | `/agent/dry-run/{email_id}` | Agent dry run (no execution) |
| GET | `/audit/{entity_type}/{entity_id}` | Audit history |