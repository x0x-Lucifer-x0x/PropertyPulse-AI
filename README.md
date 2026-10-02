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

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/properties` | List all properties |
| GET | `/api/properties/{id}` | Single property details |
| POST | `/api/properties/search` | Filtered search (location/budget/BHK/type/area) |
| POST | `/api/leads/qualify` | Score a lead from structured requirements |
| POST | `/api/affordability` | EMI/loan calculation |
| POST | `/api/chat` | Main conversational endpoint (agent + tools + RAG) |
| DELETE | `/api/chat/{session_id}` | Reset a conversation's memory |
| POST | `/api/voice/transcribe` | Speech-to-text (multipart audio upload → text) |
| POST | `/api/voice/speak` | Text-to-speech (text → sequence of base64 WAV clips) |

`POST /api/chat` body: `{"session_id": "...", "message": "..."}` — the
frontend generates a random `session_id` per browser tab and reuses it for
the conversation.

`POST /api/voice/transcribe` body: `multipart/form-data` with a `file`
field (the recorded audio clip; `webm`/`wav`/`mp3`/etc. all work).

`POST /api/voice/speak` body: `{"text": "..."}`. Returns
`{"clips": ["<base64 wav>", ...]}` — play each clip in order.

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

## Phase 2 progress

**Done:** Conversational intelligence. The agent now reads intent before
deciding how to respond, rather than treating every message as a property
query:

- Real-estate questions (properties, budgets, locations, financing, site
  visits) are still handled through the tools/database as in Phase 1.
- General questions — coding, math, writing, anything else reasonable —
  get a genuine answer instead of a deflection.
- Topic changes are followed rather than forced back to real estate; when
  the conversation returns to property talk, it picks up the budget/
  location/timeline the person already gave, without re-asking.
- Ambiguous requests get one concise clarifying question instead of a
  guess.
- The assistant doesn't repeatedly announce what it is — it just behaves
  like a capable conversational partner, in and out of real-estate topics.

This only required a system-prompt rewrite (`backend/app/llm.py`) — no new
tools or endpoints — since the underlying tool-calling loop already
supports the model choosing not to call a tool.

Also removed all demo/instructional framing from the product surface
(the "this is demo data" banner, explanatory onboarding copy, the "AI
Sales Assistant" eyebrow label) so it reads as a real product rather than
a showcase. The one exception is the developer-facing message that
appears only if `GROQ_API_KEY` is missing — that's an operator error
state, not user-facing demo copy.

**Done:** RAG over property and domain knowledge. A new `search_knowledge_base`
tool lets the agent answer open-ended questions — "what does RERA mean",
"tell me about Whitefield", "something with a golf-course view" — that
simple structured filters can't handle well.

- Pipeline: chunking → TF-IDF embeddings → FAISS (`backend/app/rag/`),
  with an automatic numpy-cosine-similarity fallback if FAISS isn't
  available on a given host.
- Indexes two kinds of content: curated domain knowledge (RERA, BHK, EMI,
  possession-status terms, and a short overview of each of the 10
  Bangalore localities in the seed data) and the live property data
  itself (name, location, amenities, description) — so descriptive/vibe
  queries can surface the right listing even when the person doesn't
  name a filterable attribute.
- Deliberately **not** a neural embedding model: TF-IDF needs no API key,
  no model download at runtime, and no GPU — important for a lean,
  low-cost host. It's swappable for a neural embedder later via the same
  `RAGIndex` interface if retrieval quality needs to improve.
- The index builds once at backend startup (`main.py`) against whatever
  properties are in the database at the time, and is cached in memory.
- Same anti-hallucination rule as Phase 1: the agent only states what a
  retrieved chunk actually says; if nothing relevant comes back, it says
  so rather than guessing.

**Done:** Voice (push-to-talk STT, spoken replies via TTS). Both reuse the
existing Groq client/API key — no extra provider:

- `POST /api/voice/transcribe` — accepts a recorded audio clip, transcribes
  it with Groq's hosted Whisper (`whisper-large-v3-turbo`).
- `POST /api/voice/speak` — takes reply text, synthesizes it with Groq's
  hosted Orpheus TTS (`canopylabs/orpheus-v1-english`). Orpheus caps input
  at ~200 characters per call, so replies are split on sentence boundaries
  into multiple WAV clips, returned together, and played back-to-back on
  the frontend (`lib/audio.ts`).
- Frontend: a hold-to-talk mic button next to the message box records via
  `MediaRecorder`, sends the clip to `/api/voice/transcribe`, and sends
  the transcribed text as a normal chat message. A "Spoken replies"
  toggle, when on, speaks each assistant reply automatically.
- Both endpoints fail with a clean `503` and a plain-language message
  (not a crash) if the Groq API is unreachable or misconfigured, same
  error-handling pattern as the chat endpoint.
- This is push-to-talk by design, per the build brief — no WebRTC, no
  continuous/always-listening mode.

**Not built yet:** CRM (lead list, site-visit scheduling),
conversation-intelligence auto-summaries, and an agent evaluation suite.
Say which to build next, or say "GO TO PRODUCTION" for Phase 3 hardening
once Phase 2 is complete.

### Voice setup note

No extra configuration needed beyond the `GROQ_API_KEY` you already have —
both STT and TTS run on Groq. If your browser blocks microphone access,
check the site permission in your browser's address-bar icon.
