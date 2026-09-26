# PropertyPulse AI

An AI real-estate sales assistant for a Bangalore property brokerage. A
prospective buyer describes what they want in plain language; the assistant
extracts their requirements, searches real listings, explains why each match
fits, answers follow-up questions, scores the lead, and recommends a next
step (e.g. schedule a site visit).

**This is Phase 1**: a deployable core product. See `PHASE 2 / 3` below for
what's intentionally left out for now (voice, RAG, CRM, auth, etc.) and why.

> **Demo data notice**: all 22 properties in `backend/seed_data.py` are
> fictional/illustrative. The UI and this README both say so — don't present
> them as live inventory.

---

## Architecture

```
Browser (Next.js/React, Vercel)
        │  HTTPS/JSON
        ▼
FastAPI backend (Railway/Render/Fly, etc.)
        │            │
        │            └── Groq LLM (tool-calling loop)
        ▼
Supabase Postgres (properties, leads)
```

- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS. Single
  chat interface with inline property-match cards and a live lead-scoring
  sidebar.
- **Backend**: FastAPI + SQLAlchemy. One agent, four tools
  (`search_properties`, `get_property_details`, `calculate_affordability`,
  `qualify_lead`), all executing real queries/logic — nothing is faked.
- **LLM**: Groq (Llama 3.3 70B by default), OpenAI-style function/tool
  calling.
- **Database**: any Postgres works; documented here for Supabase. A SQLite
  fallback (`USE_SQLITE_FALLBACK=true`) is available for local dev without
  Supabase set up yet — do not use it in production.

Lead scoring is a deterministic function, not an LLM call, so it's
consistent and auditable rather than varying between runs.

---

## Project layout

```
property-pulse-ai/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, error handling
│   │   ├── config.py          # env settings
│   │   ├── database.py        # SQLAlchemy engine/session
│   │   ├── models.py          # Property, Lead
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── llm.py             # Groq tool-calling agent loop
│   │   ├── tools/             # search, details, affordability, lead scoring
│   │   └── routers/           # chat, properties, leads
│   ├── seed_data.py           # 22 demo Bangalore properties
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── app/                   # Next.js App Router (layout, page, globals.css)
    ├── components/            # ChatPanel, MessageBubble, PropertyCard, LeadPanel
    ├── lib/                   # api.ts, types.ts, format.ts
    ├── package.json
    └── .env.example
```

---

## 1. Run the backend locally

```bash
cd backend
python -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt

cp .env.example .env
# edit .env: set GROQ_API_KEY, and either DATABASE_URL (Supabase) or
# leave USE_SQLITE_FALLBACK=true for a quick local run

python seed_data.py        # seeds ~22 demo properties (skips if already seeded)
uvicorn app.main:app --reload --port 8000
```

Check it's alive: `curl http://localhost:8000/health` → `{"status":"ok"}`

## 2. Run the frontend locally

```bash
cd frontend
npm install
cp .env.example .env.local
# NEXT_PUBLIC_API_URL should point at your backend, e.g. http://localhost:8000

npm run dev
```

Open http://localhost:3000.

## 3. Required environment variables

**Backend (`backend/.env`)**

| Variable | Required | Notes |
|---|---|---|
| `GROQ_API_KEY` | Yes (for AI chat) | From https://console.groq.com/keys |
| `GROQ_MODEL` | No | Defaults to `llama-3.3-70b-versatile` |
| `DATABASE_URL` | Yes in production | Postgres connection string (Supabase) |
| `USE_SQLITE_FALLBACK` | No | `true` for local dev without Supabase. Never use in production. |
| `ALLOWED_ORIGINS` | Yes | Comma-separated list of frontend origins for CORS |

**Frontend (`frontend/.env.local`)**

| Variable | Required | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | URL of the deployed/local backend |

## 4. Configure Supabase

1. Create a project at https://supabase.com.
2. Project Settings → Database → Connection string → URI. Copy it and fill
   in your database password.
3. Paste that as `DATABASE_URL` in `backend/.env` (and in your backend
   host's env vars for production).
4. Run `python seed_data.py` once against that database (locally, pointed
   at the Supabase URL) to create tables and seed demo data. You can also
   run it from CI/CD or a one-off shell on your hosting provider.

Supabase is just managed Postgres here — no Supabase-specific SDK is used,
so any Postgres instance works if you'd rather self-host.

## 5. Configure Groq

1. Create an API key at https://console.groq.com/keys.
2. Set `GROQ_API_KEY` in the backend environment.
3. `GROQ_MODEL` defaults to `llama-3.3-70b-versatile`; change it if you
   want a different Groq-hosted model, as long as it supports tool calling.

If the key is missing or invalid, or the Groq API is unreachable, the
`/api/chat` endpoint degrades gracefully with a clear error message instead
of crashing — the rest of the app (property browsing, search, affordability,
lead-qualify endpoints) keeps working independently of the LLM.

## 6. Deploy the frontend (Vercel)

1. Push this repo to GitHub.
2. In Vercel, "New Project" → import the repo → set **Root Directory** to
   `frontend`.
3. Add env var `NEXT_PUBLIC_API_URL` = your deployed backend URL.
4. Deploy. Vercel auto-detects Next.js.

## 7. Deploy the backend

Any platform that runs a Python web process works (Railway, Render, Fly.io,
etc.). General steps:

1. Point the service at the `backend/` directory.
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Set env vars: `GROQ_API_KEY`, `DATABASE_URL` (Supabase), `ALLOWED_ORIGINS`
   (your Vercel URL).
5. Run `python seed_data.py` once (a one-off shell/job on the platform, or
   locally pointed at the production `DATABASE_URL`) to seed demo data.

---

## API reference (Phase 1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/properties` | List all properties |
| GET | `/api/properties/{id}` | Single property details |
| POST | `/api/properties/search` | Filtered search (location/budget/BHK/type/area) |
| POST | `/api/leads/qualify` | Score a lead from structured requirements |
| POST | `/api/affordability` | EMI/loan calculation |
| POST | `/api/chat` | Main conversational endpoint (agent + tools) |
| DELETE | `/api/chat/{session_id}` | Reset a conversation's memory |

`POST /api/chat` body: `{"session_id": "...", "message": "..."}` — the
frontend generates a random `session_id` per browser tab and reuses it for
the conversation.

---

## What was tested

Ran locally end-to-end (backend + frontend against each other) before
delivery:

- Property search: location, budget, BHK, and combined filters (verified
  against the spec's TEST 1 — 3BHK Whitefield <₹1cr — and TEST 2 — villa
  Koramangala ₹50L, which has no exact match and correctly falls back to
  suggesting alternatives).
- Property details, including a lookup for a non-existent ID (clean 404,
  not a stack trace).
- Affordability/EMI calculation against a known amortization example.
- Lead qualification scoring and next-action logic.
- `/api/chat` degrading gracefully (clear message, no 500) when the Groq
  API is unreachable or misconfigured, instead of crashing.
- Frontend production build (`npm run build`) — compiles, type-checks, and
  statically generates cleanly.
- Frontend ↔ backend integration over HTTP with a live dev server.

Not independently testable in this environment: an actual Groq API call
(this sandbox has no network access to `api.groq.com`) and an actual
Supabase connection (needs your project's credentials). Both are standard
HTTP/Postgres calls using well-known SDKs, and the code paths around them
(tool-calling loop, error handling, DB session lifecycle) were exercised
via the SQLite fallback and the graceful-degradation path above — but you
should do one real end-to-end run with your own `GROQ_API_KEY` and
`DATABASE_URL` before treating this as fully verified in your environment.

---

## Engineering notes

- Conversation memory is in-process (a dict keyed by `session_id`), which
  is fine for a single backend instance. If you scale to multiple
  instances, move it to Redis or the database before Phase 2's CRM work —
  this is one of the "add later" seams mentioned in the build brief.
- The agent's system prompt explicitly forbids inventing property facts;
  every fact it states comes from a tool result, not from the model's own
  knowledge.
- Lead scoring is deterministic (plain Python), not an LLM call, so scores
  are reproducible.
- CORS is restricted via `ALLOWED_ORIGINS`; unhandled exceptions are
  caught globally and never leak stack traces to the client.

## Phase 2 / Phase 3 (not built yet)

Per the build brief: voice (Whisper STT/TTS), RAG over a property knowledge
base, a CRM (lead list, site-visit scheduling, conversation intelligence),
and agent evaluation suites are Phase 2. Auth, rate limiting, structured
logging, CI/CD, and other production hardening are Phase 3. Say "GO TO NEXT
PHASE" / "GO TO PRODUCTION" to continue building on top of this without a
rebuild.
