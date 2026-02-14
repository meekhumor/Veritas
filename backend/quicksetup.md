# Veritas — Quick Setup Guide

Get Veritas running locally in under 5 minutes.

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| **Python** | 3.12+ | [python.org](https://www.python.org/downloads/) |
| **uv** | latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **bun** (optional) | latest | `curl -fsSL https://bun.sh/install \| bash` |

## API Keys Required

You need at least **2 keys** to get started (Gemini + Supabase). The rest are optional but enable more evidence sources.

| Key | Where to Get It | Required? |
|---|---|---|
| **Google API Key** (Gemini) | [aistudio.google.com](https://aistudio.google.com/apikey) | **Yes** |
| **Supabase URL + Service Key** | [supabase.com](https://supabase.com) → Project Settings → API | **Yes** |
| **Tavily API Key** | [tavily.com](https://tavily.com) | Recommended |
| **Media Cloud API Key** | [mediacloud.org](https://mediacloud.org) | Optional |
| **Google Fact Check API Key** | [Google Cloud Console](https://console.cloud.google.com) → Enable Fact Check Tools API | Optional |

## Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd hackbp
```

## Step 2: Set Up the Backend

```bash
cd backend

# Copy the environment template
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```env
GOOGLE_API_KEY=your-gemini-api-key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
TAVILY_API_KEY=your-tavily-key          # optional but recommended
MEDIACLOUD_API_KEY=                      # optional
GOOGLE_FACTCHECK_API_KEY=                # optional
FRONTEND_URL=http://localhost:5173
```

Install dependencies:

```bash
uv sync
```

## Step 3: Set Up the Database

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Open the **SQL Editor**
3. Copy the contents of `backend/app/db/migrations.sql`
4. Paste and run the SQL

This creates 4 tables: `investigations`, `evidence`, `threats`, `votes` — with indexes and RLS policies.

## Step 4: Start the Backend

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Verify it's working:

```bash
curl http://localhost:8000/health
# → {"status":"ok","service":"veritas-api"}
```

API docs available at: http://localhost:8000/docs

## Step 5: Set Up the Frontend

```bash
cd ../frontend

# Install dependencies (use bun or npm)
bun install
# or: npm install

# Start dev server
bun dev
# or: npm run dev
```

Frontend runs at: http://localhost:5173

## Step 6: Verify Everything Works

1. Open http://localhost:5173 in your browser
2. You should see the Veritas landing page
3. Open http://localhost:8000/docs to see the API documentation
4. Try a test investigation:

```bash
curl -X POST http://localhost:8000/investigate/sync \
  -H "Content-Type: application/json" \
  -d '{"query": "Does 5G cause cancer?"}'
```

## Running Tests

```bash
cd backend
uv run python -m pytest tests/ -v
```

All 84 tests run with mocked APIs — no API keys needed.

## Troubleshooting

### "Module not found" errors
Make sure you're running from inside the `backend/` directory:
```bash
cd backend
uv run uvicorn app.main:app --reload
```

### Supabase connection errors
- Verify `SUPABASE_URL` starts with `https://`
- Verify `SUPABASE_SERVICE_ROLE_KEY` is the **service role** key (not the anon key)
- Make sure you've run the migration SQL

### Missing evidence sources
Agents gracefully skip when their API keys are missing. You'll see warnings in the logs like:
```
WARNING - Web Search: no Tavily API key configured
```
This is normal — the pipeline still works with whatever sources are available.

### CORS errors in browser
Set `FRONTEND_URL` in `.env` to match your frontend's URL (default: `http://localhost:5173`).
