# Veritas — Deployment Guide

## Deployment Options

Veritas backend is a standard FastAPI app that can be deployed to any platform supporting Python 3.12. The frontend is a static React/Vite build.

---

## Option 1: Railway (Recommended for Hackathons)

Railway offers one-click deployment with free tier credits.

### Backend

1. Push your code to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select the `backend` directory as the root
4. Set the start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Add environment variables in Railway dashboard:
   - `GOOGLE_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `TAVILY_API_KEY`
   - `FRONTEND_URL` (set to your deployed frontend URL)
6. Railway auto-detects `pyproject.toml` and installs with `uv`

### Frontend

1. Add another service in the same Railway project
2. Select the `frontend` directory
3. Set build command: `bun install && bun run build`
4. Set start command: `npx serve dist -s -l $PORT`
5. Add env var: `VITE_API_URL` pointing to your backend URL

---

## Option 2: Render

### Backend

1. Create a new **Web Service** on [render.com](https://render.com)
2. Connect your GitHub repo
3. Settings:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install uv && uv sync`
   - **Start Command**: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
4. Add environment variables in the Render dashboard

### Frontend

1. Create a new **Static Site** on Render
2. Settings:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `frontend/dist`

---

## Option 3: Fly.io

### Backend

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app/ app/

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Deploy:

```bash
cd backend
fly launch --name veritas-api
fly secrets set GOOGLE_API_KEY=xxx SUPABASE_URL=xxx SUPABASE_SERVICE_ROLE_KEY=xxx
fly deploy
```

### Frontend

Create `frontend/Dockerfile`:

```dockerfile
FROM node:20-slim AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

---

## Option 4: VPS / Docker Compose

Create `docker-compose.yml` at the project root:

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

```bash
docker compose up -d
```

---

## Database Setup (All Options)

Regardless of deployment method, you need to run the Supabase migration:

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Open **SQL Editor**
3. Paste and run `backend/app/db/migrations.sql`

The backend uses the **service role key** to bypass RLS — this is intentional for server-side access.

---

## Environment Variables Reference

| Variable | Required | Production Notes |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini 2.0 Flash. Consider rate limits. |
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | **Keep secret** — bypasses RLS |
| `TAVILY_API_KEY` | Recommended | Free tier: 1,000 searches/month |
| `MEDIACLOUD_API_KEY` | Optional | For news source scanning |
| `GOOGLE_FACTCHECK_API_KEY` | Optional | Google Fact Check Tools API |
| `FRONTEND_URL` | Yes | Set to deployed frontend URL for CORS |
| `DEBUG` | No | Set to `false` in production |

---

## Production Checklist

- [ ] All API keys set as environment variables (never in code)
- [ ] `FRONTEND_URL` set to actual frontend domain
- [ ] `DEBUG` set to `false`
- [ ] Supabase migration SQL executed
- [ ] RLS policies active on all tables
- [ ] HTTPS enabled (most platforms handle this automatically)
- [ ] Health check endpoint (`/health`) monitored
- [ ] Log aggregation configured (stdout is sufficient for most platforms)

---

## Scaling Notes

- **LLM calls** are the bottleneck — each investigation makes 4 LLM calls (query analyzer, cross-reference, impact, verdict)
- **Evidence gathering** is I/O-bound — all 4 sub-agents run sequentially in the pipeline but each is async
- **Early Warning Engine** runs as a single background task — no horizontal scaling needed for hackathon scale
- **SSE connections** are long-lived — ensure your platform supports persistent HTTP connections
- Supabase free tier handles thousands of concurrent connections
