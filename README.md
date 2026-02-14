# Veritas — Multi-Source Misinformation & Social Risk Early Warning System

Veritas is an AI-powered platform that investigates claims in real-time by cross-referencing news, fact-checkers, and authoritative sources. It features a 6-agent LangGraph investigation pipeline, a community feed of published investigations, and an early warning system that detects misinformation spikes.

---

## Features

-  **AI Investigation Pipeline** — 6-agent LangGraph pipeline (query analysis → clarification → evidence gathering → cross-reference → impact assessment → verdict synthesis) with real-time SSE streaming
-  **Verdict System** — Claims rated as TRUE, FALSE, PARTIALLY TRUE, MISLEADING, or UNVERIFIED with confidence scores
-  **Multi-Source Evidence** — Cross-references web search (Tavily), news (Media Cloud), authoritative sources, and fact-check databases
-  **Impact Assessment** — Scores claims across 5 dimensions: topic sensitivity, geographic reach, emotional charge, actionability, and vulnerable populations
-  **Community Feed** — Browse, filter, sort, and upvote/flag published investigations
-  **Early Warning System** — Background engine detects misinformation spikes every 2 minutes and broadcasts real-time SSE alerts
-  **Dark/Light Theme** — Warm amber/stone design system with full dark mode support
-  **Authentication** — Supabase Auth with email/password and Google OAuth

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI |
| AI Pipeline | LangGraph + LangChain |
| LLM | Google Gemini (via LangChain) |
| Database | Supabase (PostgreSQL + RLS) |
| Search APIs | Tavily, Media Cloud, Google Fact Check |
| Streaming | Server-Sent Events (SSE) |
| Package Manager | uv |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | React 19 |
| Build Tool | Vite 8 |
| Styling | Tailwind CSS v4 |
| State Management | Zustand |
| HTTP Client | Axios |
| Routing | React Router v7 |
| Auth | Supabase JS |
| Icons | Lucide React |
| Notifications | Sonner |
| Package Manager | Bun |

---

## Project Structure

```
hackbp/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # App entry, CORS, lifespan
│   │   ├── agents/             # 6-agent LangGraph pipeline
│   │   │   ├── pipeline.py     # Pipeline orchestrator
│   │   │   ├── query_analyzer.py
│   │   │   ├── clarifier.py
│   │   │   ├── evidence_gatherer.py
│   │   │   ├── cross_reference.py
│   │   │   ├── impact_assessor.py
│   │   │   └── verdict_synthesizer.py
│   │   ├── api/                # Route handlers
│   │   │   ├── investigate.py  # /investigate (SSE + sync)
│   │   │   ├── feed.py         # /feed (paginated + trending)
│   │   │   ├── threats.py      # /threats (active + SSE stream)
│   │   │   └── health.py
│   │   ├── core/               # Config, DB, LLM setup
│   │   ├── models/             # Pydantic schemas
│   │   ├── services/           # Spam filter, early warning engine
│   │   └── db/                 # Migrations
│   └── tests/                  # Pytest test suite
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── App.jsx             # Routes & providers
│   │   ├── stores/             # Zustand state management
│   │   │   ├── investigation-store.js
│   │   │   ├── feed-store.js
│   │   │   └── threats-store.js
│   │   ├── lib/
│   │   │   ├── api.js          # Axios instance + SSE helpers
│   │   │   ├── supabase.js     # Supabase client
│   │   │   └── utils.js
│   │   ├── pages/
│   │   │   ├── landing.jsx     # Hero + feature overview
│   │   │   ├── investigate.jsx # Claim input + SSE progress + report
│   │   │   ├── feed.jsx        # Paginated investigation feed
│   │   │   ├── report-detail.jsx # Full investigation report
│   │   │   ├── threats.jsx     # Early warning threat dashboard
│   │   │   ├── dashboard.jsx   # User dashboard + quick investigate
│   │   │   ├── login.jsx
│   │   │   └── signup.jsx
│   │   ├── components/
│   │   │   ├── navbar.jsx
│   │   │   ├── verdict-badge.jsx
│   │   │   ├── confidence-meter.jsx
│   │   │   ├── impact-chart.jsx
│   │   │   ├── evidence-card.jsx
│   │   │   ├── investigation-card.jsx
│   │   │   ├── agent-progress.jsx
│   │   │   ├── threat-alert-card.jsx
│   │   │   ├── cross-reference-section.jsx
│   │   │   └── ui/             # Base UI primitives (shadcn-style)
│   │   └── context/
│   │       └── auth-context.jsx
│   └── index.html
│
├── BACKEND_SYNOPSIS.md         # Full API documentation
└── README.md                   # This file
```

---

## Getting Started

### Prerequisites

- [Bun](https://bun.sh) (frontend)
- [uv](https://docs.astral.sh/uv/) (backend)
- [Supabase](https://supabase.com) project (database + auth)
- API keys: Google Gemini, Tavily (search), optionally Media Cloud & Google Fact Check

### 1. Clone the repository

```bash
git clone <repo-url>
cd hackbp
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
uv sync

# Create .env file
cp .env.example .env  # or create manually
```

**Backend `.env`:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
GOOGLE_API_KEY=your-gemini-api-key
TAVILY_API_KEY=your-tavily-key
FRONTEND_URL=http://localhost:5173
# Optional:
MEDIACLOUD_API_KEY=your-mediacloud-key
GOOGLE_FACTCHECK_API_KEY=your-factcheck-key
```

```bash
# Run the backend
uv run uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000` (API docs at `/docs`).

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
bun install

# Create .env file
```

**Frontend `.env`:**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

```bash
# Run the frontend
bun run dev
```

Frontend will be available at `http://localhost:5173`.

---

## Pages & Routes

| Route | Page | Auth Required | Description |
|-------|------|:---:|-------------|
| `/` | Landing | No | Hero, features, pipeline overview |
| `/investigate` | Investigate | No | Submit a claim → real-time SSE progress → full report |
| `/feed` | Feed | No | Paginated, filterable feed of published investigations |
| `/feed/:id` | Report Detail | No | Full investigation report with voting |
| `/threats` | Threats | No | Live early warning threat dashboard |
| `/dashboard` | Dashboard | Yes | User dashboard with quick-investigate |
| `/login` | Login | No | Email/password + Google OAuth |
| `/signup` | Signup | No | Account creation |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API info |
| `GET` | `/health` | Health check |
| `POST` | `/investigate` | SSE streaming investigation |
| `POST` | `/investigate/sync` | Non-streaming investigation |
| `GET` | `/feed` | Paginated investigation feed |
| `GET` | `/feed/trending` | Trending investigation clusters |
| `GET` | `/feed/:id` | Single investigation report |
| `POST` | `/feed/:id/vote` | Upvote or flag an investigation |
| `GET` | `/threats/active` | Active early warning threats |
| `GET` | `/threats/stream` | SSE stream for real-time threat alerts |

See [BACKEND_SYNOPSIS.md](BACKEND_SYNOPSIS.md) for full API documentation with request/response schemas.

---

## Running Tests

```bash
cd backend
uv run pytest
```

---

## License

MIT
