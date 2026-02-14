# Veritas Backend

Multi-Source Misinformation & Social Risk Early Warning System — FastAPI backend.

## Setup

```bash
cd backend
cp .env.example .env   # fill in your API keys
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

## Architecture

- **FastAPI** — REST + SSE endpoints
- **LangGraph** — 6-agent investigation pipeline
- **LangChain + Gemini 2.0 Flash** — LLM orchestration
- **Supabase** — PostgreSQL database
- **Tavily / Media Cloud / Google Fact Check** — Evidence sources
