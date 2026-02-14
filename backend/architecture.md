# Veritas — System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                      │
│  Landing → Investigation UI → Live Feed → Threat Dashboard          │
└──────────────┬──────────────────────────┬───────────────────────────┘
               │ REST + SSE              │ SSE (threats)
               ▼                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python 3.12)                    │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐    │
│  │ /investigate │  │   /feed      │  │  /threats               │    │
│  │  (SSE)      │  │  (REST)      │  │  (REST + SSE stream)    │    │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬──────────────┘    │
│         │                │                      │                   │
│  ┌──────▼──────┐         │           ┌──────────▼──────────────┐    │
│  │ Spam Filter │         │           │  Early Warning Engine   │    │
│  └──────┬──────┘         │           │  (background loop)      │    │
│         │                │           └─────────────────────────┘    │
│  ┌──────▼──────────────────────────────────────────────────┐       │
│  │              LangGraph Investigation Pipeline            │       │
│  │  Agent 1 → 2 → 3a,3b,3c,3d → 4 → 5 → 6               │       │
│  └──────────────────────┬──────────────────────────────────┘       │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────────┐
        │                  │                      │
   ┌────▼────┐      ┌─────▼──────┐        ┌──────▼──────┐
   │ Gemini  │      │  External  │        │  Supabase   │
   │ 2.0     │      │  APIs      │        │  (Postgres) │
   │ Flash   │      │            │        │             │
   └─────────┘      └────────────┘        └─────────────┘
```

## Agent Pipeline Architecture

The investigation pipeline is a compiled **LangGraph StateGraph** where each agent is a node that reads from and writes to shared `InvestigationState`.

### Pipeline Flow

```
                    ┌───────────────────┐
                    │  Query Analyzer   │  Agent 1
                    │  (classify query) │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │    Clarifier      │  Agent 2
                    │  (refine if vague)│
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──┐  ┌───────▼────┐  ┌──────▼──────┐
    │ Web Search │  │News Scanner│  │  Authority  │  Agent 3
    │  (Tavily)  │  │(MediaCloud)│  │  Checker    │  (4 sub-agents)
    └─────────┬──┘  └───────┬────┘  └──────┬──────┘
              │              │              │
              └──────────────┼──────────────┘
                             │
                    ┌────────▼──────────┐
                    │  Fact-Check       │  Agent 3d
                    │  Lookup (Google)  │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │ Cross-Reference   │  Agent 4
                    │ Analyzer          │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │ Impact Assessor   │  Agent 5
                    │ (5 dimensions)    │
                    └────────┬──────────┘
                             │
                    ┌────────▼──────────┐
                    │ Verdict           │  Agent 6
                    │ Synthesizer       │
                    └─────────────────── ┘
```

### Agent Details

| # | Agent | Input | Output | LLM? |
|---|---|---|---|---|
| 1 | **Query Analyzer** | Raw user query | `refined_query`, `category`, `needs_clarification` | Yes |
| 2 | **Clarifier** | Query + clarification answers | Further-refined query | Yes (conditional) |
| 3a | **Web Search** | Refined query | `evidence[]` (web results) | No (API) |
| 3b | **News Scanner** | Refined query | `evidence[]` (news articles) | No (API) |
| 3c | **Authority Checker** | Refined query | `evidence[]` (authority sites) | No (API) |
| 3d | **Fact-Check Lookup** | Refined query | `evidence[]` (fact-checks) | No (API) |
| 4 | **Cross-Reference** | All evidence | `consensus_points`, `contradictions`, `source_agreement_score` | Yes |
| 5 | **Impact Assessor** | Evidence + cross-ref | `impact` (5-dimension score 0-100) | Yes |
| 6 | **Verdict Synthesizer** | Everything above | `verdict`, `confidence`, `summary` | Yes |

### Shared State (`InvestigationState`)

All agents read from and write to a shared Pydantic model with annotated reducers:

```python
class InvestigationState(BaseModel):
    # Input
    query: str
    investigation_id: str

    # Agent 1 outputs
    refined_query: str
    category: Category
    needs_clarification: bool
    clarification_questions: list[str]

    # Agent 3 outputs (reducers merge lists)
    evidence: Annotated[list[EvidenceItem], merge_evidence]
    web_search_done: bool
    news_scan_done: bool
    authority_check_done: bool
    fact_check_done: bool

    # Agent 4 output
    cross_reference: CrossReferenceResult

    # Agent 5 output
    impact: ImpactScore

    # Agent 6 output
    verdict: Verdict          # TRUE | FALSE | UNVERIFIED | PARTIALLY_TRUE | MISLEADING
    confidence: float         # 0.0 - 1.0
    summary: str

    # Audit trail (reducer appends)
    investigation_trail: Annotated[list[str], merge_trail]
```

## Data Model

### Database Tables (Supabase/PostgreSQL)

```
investigations
├── id (UUID, PK)
├── query (TEXT)
├── refined_query (TEXT)
├── category (TEXT)
├── verdict (TEXT)
├── confidence (FLOAT)
├── summary (TEXT)
├── impact (JSONB)
├── cross_reference (JSONB)
├── investigation_trail (TEXT[])
├── upvotes (INT, default 0)
├── flags (INT, default 0)
├── is_published (BOOL, default true)
└── created_at (TIMESTAMPTZ)

evidence
├── id (UUID, PK)
├── investigation_id (UUID, FK → investigations)
├── source_type (TEXT)
├── source_name (TEXT)
├── source_url (TEXT)
├── title (TEXT)
├── content (TEXT)
├── credibility_score (FLOAT)
└── retrieved_at (TIMESTAMPTZ)

threats
├── id (UUID, PK)
├── title (TEXT)
├── description (TEXT)
├── status (TEXT)  -- active | monitoring | resolved
├── representative_query (TEXT)
├── investigation_count (INT)
├── avg_impact (FLOAT)
├── first_seen (TIMESTAMPTZ)
└── last_updated (TIMESTAMPTZ)

votes
├── id (UUID, PK)
├── investigation_id (UUID, FK → investigations)
├── user_id (TEXT)
├── vote_type (TEXT)  -- upvote | flag
└── created_at (TIMESTAMPTZ)
  UNIQUE(investigation_id, user_id, vote_type)
```

## Impact Assessment Dimensions

The Impact Assessor scores misinformation risk across 5 dimensions (0-100 each):

| Dimension | What it Measures |
|---|---|
| **Topic Sensitivity** | How sensitive is the subject area (health, elections, etc.) |
| **Geographic Reach** | Local vs. national vs. global scope |
| **Emotional Charge** | How emotionally provocative is the claim |
| **Actionability** | Could this claim lead people to take harmful actions |
| **Vulnerable Populations** | Does it disproportionately affect vulnerable groups |

The **overall score** is calculated from these 5 dimensions by the LLM.

## SSE Streaming Protocol

### Investigation Stream (`POST /investigate`)

The investigation endpoint streams `AgentStepEvent` objects as SSE:

```
event: agent_step
data: {"agent": "query_analyzer", "status": "running", "message": "Analyzing query..."}

event: agent_step
data: {"agent": "query_analyzer", "status": "completed", "message": "Classified as HEALTH"}

event: agent_step
data: {"agent": "web_search", "status": "running", "message": "Searching..."}

...

event: complete
data: {"investigation_id": "uuid", "verdict": "FALSE", "confidence": 0.87, ...}
```

### Threat Stream (`GET /threats/stream`)

Broadcasts new threats via a pub/sub `ThreatEventBus`:

```
event: threat
data: {"title": "Spike: vaccine misinformation", "count": 5, "avg_impact": 78.5}

event: ping
data: {"type": "keepalive"}
```

## Early Warning Engine

A background async loop (`asyncio.create_task`) that runs every 120 seconds:

1. **Fetch** — Gets recent investigations from the last 6 hours
2. **Cluster** — Groups similar claims by keyword overlap (Jaccard similarity, threshold 0.6)
3. **Detect** — Flags clusters with ≥3 claims and average impact > 60 as spikes
4. **Save** — Persists new threats to the database
5. **Broadcast** — Pushes threat events to all SSE subscribers via `ThreatEventBus`

## Spam Filter

Two-stage spam detection:

1. **Fast Heuristics** — Reject queries < 3 chars or > 1000 chars
2. **LLM Classification** — Gemini classifies as `genuine | spam | abusive | off_topic`

Fails open: if the LLM check errors, the query is allowed through.

## Security

- **CORS** — Configured for frontend origin only
- **Row Level Security (RLS)** — Supabase tables use RLS policies; backend uses service role key to bypass
- **Input Validation** — Pydantic models with length constraints on all inputs
- **Spam Filter** — Screens queries before invoking the expensive agent pipeline
