# Veritas — Multi-Source Misinformation & Social Risk Early Warning System

> AI-powered fact-checking platform that investigates claims across multiple sources, scores societal impact, and detects emerging misinformation spikes in real time.

## Overview

Veritas is a hackathon project built for rapid misinformation analysis. It combines a **6-agent LangGraph pipeline** with multi-source evidence gathering to produce structured investigation reports — complete with verdicts, confidence scores, and societal impact ratings.

### Key Features

- **6-Agent Investigation Pipeline** — Query analysis → Clarification → Evidence gathering → Cross-referencing → Impact assessment → Verdict synthesis
- **Multi-Source Evidence** — Tavily web search, Media Cloud news scanning (50K+ outlets), Google Fact Check API, authority site checks (WHO, CDC, gov domains)
- **Real-Time SSE Streaming** — Watch investigations unfold step-by-step via Server-Sent Events
- **Early Warning Engine** — Background spike detection clusters similar claims and broadcasts emerging threats
- **Spam Filter** — LLM-based query screening with fast heuristic fallbacks
- **Community Feed** — Browse/vote on investigation reports, filter by category, sort by recency/impact/trending

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI (Python 3.12) |
| **Agent Orchestration** | LangGraph + LangChain |
| **LLM** | Gemini 2.0 Flash (via `langchain-google-genai`) |
| **Web Search** | Tavily API |
| **News Scanning** | Media Cloud API |
| **Fact Checking** | Google Fact Check Tools API |
| **Database** | Supabase (PostgreSQL) |
| **Streaming** | SSE via `sse-starlette` |
| **Package Manager** | uv |
| **Frontend** | React 19 + Vite 8 + TailwindCSS v4 |

## Project Structure

```
backend/
├── app/
│   ├── agents/                # LangGraph investigation pipeline
│   │   ├── state.py           # Shared InvestigationState schema
│   │   ├── query_analyzer.py  # Agent 1: Parse & classify query
│   │   ├── clarifier.py       # Agent 2: Refine ambiguous queries
│   │   ├── evidence_gatherer.py  # Agent 3: 4 parallel sub-agents
│   │   ├── cross_reference.py # Agent 4: Find consensus & contradictions
│   │   ├── impact_assessor.py # Agent 5: Score societal risk (5 dimensions)
│   │   ├── verdict_synthesizer.py  # Agent 6: Final verdict + confidence
│   │   └── pipeline.py        # LangGraph StateGraph compilation
│   ├── api/                   # FastAPI route handlers
│   │   ├── investigate.py     # POST /investigate (SSE), POST /investigate/sync
│   │   ├── feed.py            # GET /feed, GET /feed/trending, votes
│   │   ├── threats.py         # GET /threats/active, GET /threats/stream (SSE)
│   │   └── health.py          # Health check
│   ├── core/                  # Shared utilities
│   │   ├── config.py          # Pydantic Settings (env vars)
│   │   ├── database.py        # Supabase CRUD operations
│   │   ├── llm.py             # Gemini LLM factory
│   │   └── supabase.py        # Supabase client singleton
│   ├── models/
│   │   └── schemas.py         # All Pydantic models & enums
│   ├── services/
│   │   ├── spam_filter.py     # LLM-based spam detection
│   │   └── early_warning.py   # Background spike detection engine
│   ├── db/
│   │   └── migrations.sql     # Supabase table definitions & RLS policies
│   └── main.py                # FastAPI app with lifespan & middleware
├── tests/                     # 84 tests (pytest + pytest-asyncio)
│   ├── test_agents/           # Agent unit tests (mocked LLM)
│   ├── test_services/         # Service tests (spam filter, early warning)
│   ├── test_models.py         # Schema validation tests
│   ├── test_feed.py           # Feed API tests
│   ├── test_investigate.py    # Investigation API tests
│   ├── test_threats.py        # Threats API tests
│   └── test_health.py         # Health endpoint tests
├── pyproject.toml             # Dependencies & pytest config
├── .env.example               # Required environment variables
├── architecture.md            # System architecture documentation
├── quicksetup.md              # Quick setup guide
└── deploy.md                  # Deployment guide
```

## Quick Start

```bash
# 1. Clone and enter the backend
cd backend

# 2. Set up environment variables
cp .env.example .env
# Fill in: GOOGLE_API_KEY, TAVILY_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# 3. Install dependencies
uv sync

# 4. Run the Supabase migration
# Copy contents of app/db/migrations.sql into Supabase SQL Editor and execute

# 5. Start the server
uv run uvicorn app.main:app --reload --port 8000
```

API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/investigate` | Start investigation (SSE streaming) |
| `POST` | `/investigate/sync` | Start investigation (JSON response) |
| `GET` | `/feed` | Browse investigation reports |
| `GET` | `/feed/trending` | Trending claim clusters |
| `GET` | `/feed/{id}` | Get specific investigation |
| `POST` | `/feed/{id}/vote` | Upvote or flag a report |
| `GET` | `/threats/active` | Active threat alerts |
| `GET` | `/threats/stream` | Real-time threat SSE stream |
| `GET` | `/health` | Health check |

## Running Tests

```bash
cd backend
uv run python -m pytest tests/ -v
```

84 tests covering all agents, API endpoints, services, and models. All tests use mocked LLM/API calls — no API keys needed for testing.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini 2.0 Flash API key |
| `TAVILY_API_KEY` | Recommended | Web search & authority checking |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service role key |
| `MEDIACLOUD_API_KEY` | Optional | News scanning (50K+ outlets) |
| `GOOGLE_FACTCHECK_API_KEY` | Optional | Google Fact Check Tools API |
| `FRONTEND_URL` | Optional | CORS origin (default: `http://localhost:5173`) |

## Documentation

- [Architecture](architecture.md) — System design, agent pipeline, data flow
- [Quick Setup](quicksetup.md) — Step-by-step setup guide
- [Deployment](deploy.md) — Production deployment guide

## License

Built for hackathon use. MIT License.
