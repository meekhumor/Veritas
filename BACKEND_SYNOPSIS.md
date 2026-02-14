# Veritas Backend — Complete Synopsis for Frontend Development

> **Project:** Veritas — Multi-Source Misinformation & Social Risk Early Warning System  
> **Backend:** FastAPI + LangGraph + LangChain + Supabase  
> **Status:** Fully functional, tested end-to-end  
> **Backend URL:** `http://localhost:8000` (dev)  
> **Frontend URL:** `http://localhost:5173` (configured in CORS)

---

## 1. API Endpoints

### `GET /`
Returns API info.
```json
{ "name": "Veritas API", "version": "0.1.0", "docs": "/docs" }
```

### `GET /health`
Health check.
```json
{ "status": "ok", "service": "veritas-api" }
```

---

### `POST /investigate` (SSE Streaming)
**Content-Type:** `application/json`  
**Response:** `text/event-stream` (Server-Sent Events)

Runs the 6-agent investigation pipeline, streaming progress events in real-time.

**Request Body:**
```json
{
  "query": "Does 5G cause cancer?",
  "category": null  // optional: "Health" | "Finance" | "Politics" | "Tech" | "General"
}
```

**SSE Events emitted (in order):**
```
event: started
data: {"agent": "pipeline", "status": "started", "message": "Investigation started: Does 5G cause cancer?", "data": {"investigation_id": "uuid"}, "timestamp": "..."}

event: completed
data: {"agent": "query_analyzer", "status": "completed", "message": "Query Analyzer completed", "data": null, "timestamp": "..."}

event: completed
data: {"agent": "clarifier", "status": "completed", "message": "Clarifier completed", ...}

event: completed
data: {"agent": "web_search", "status": "completed", "message": "Web Search completed", ...}

event: completed
data: {"agent": "news_scanner", "status": "completed", ...}

event: completed
data: {"agent": "authority_checker", "status": "completed", ...}

event: completed
data: {"agent": "fact_check_lookup", "status": "completed", ...}

event: completed
data: {"agent": "cross_reference_analyzer", "status": "completed", ...}

event: completed
data: {"agent": "impact_assessor", "status": "completed", ...}

event: completed
data: {"agent": "verdict_synthesizer", "status": "completed", ...}

event: completed
data: {"agent": "pipeline", "status": "completed", "message": "Investigation complete", "data": { <FULL INVESTIGATION REPORT> }, "timestamp": "..."}
```

**Error event:**
```
event: error
data: {"agent": "pipeline", "status": "error", "message": "Investigation failed: ...", "data": {"investigation_id": "...", "error": "..."}, "timestamp": "..."}
```

**Frontend SSE usage example:**
```javascript
const eventSource = new EventSource('/investigate'); // Won't work for POST

// Use fetch with ReadableStream instead:
const response = await fetch('http://localhost:8000/investigate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: "Does 5G cause cancer?" }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  buffer += decoder.decode(value, { stream: true });
  
  // Parse SSE lines
  const lines = buffer.split('\n');
  buffer = lines.pop(); // Keep incomplete line in buffer
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      // Handle agent step event
      console.log(data.agent, data.status, data.message);
      
      if (data.agent === 'pipeline' && data.status === 'completed') {
        const report = data.data; // Full InvestigationReport
      }
    }
  }
}
```

---

### `POST /investigate/sync` (Non-Streaming)
**Content-Type:** `application/json`  
**Response:** `application/json`

Same pipeline but returns the full report when done (no streaming). Takes ~60 seconds.

**Request Body:**
```json
{
  "query": "Does 5G cause cancer?",
  "category": null
}
```

**Response (200):** Full `InvestigationReport` object (see schema below).

**Error responses:**
- `400` — Spam/abuse detected: `{ "detail": "Query rejected: <reason>" }`
- `429` — LLM rate limit exceeded: `{ "detail": "LLM rate limit exceeded..." }`
- `503` — LLM model not available: `{ "detail": "LLM model not available: ..." }`
- `500` — Generic failure: `{ "detail": "Investigation failed. Please try again." }`

---

### `GET /feed`
Paginated public feed of published investigations.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `category` | string | null | Filter: `Health`, `Finance`, `Politics`, `Tech`, `General` |
| `sort` | string | `"recent"` | Sort: `recent`, `impact`, `trending` |
| `page` | int | 1 | Page number (1-indexed) |
| `limit` | int | 20 | Items per page (1-100) |

**Response (200):**
```json
{
  "items": [ /* array of InvestigationReport objects */ ],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

---

### `GET /feed/trending`
Get trending claim clusters (most upvoted published investigations).

**Response (200):**
```json
{
  "clusters": [
    {
      "id": "uuid",
      "query": "Does 5G cause cancer?",
      "category": "Health",
      "verdict": "FALSE",
      "confidence": 0.85,
      "upvotes": 12,
      "created_at": "2026-02-14T..."
    }
  ]
}
```

---

### `GET /feed/{investigation_id}`
Get a single investigation report by ID.

**Response (200):** Full `InvestigationReport` object.  
**Response (404):** `{ "detail": "Investigation not found" }`

---

### `POST /feed/{investigation_id}/vote`
Upvote or flag an investigation.

**Request Body:**
```json
{
  "vote_type": "upvote",  // "upvote" | "flag"
  "user_id": "uuid-of-user"
}
```

**Response (200):**
```json
{ "status": "ok", "vote_type": "upvote" }
```

---

### `GET /threats/active`
Get currently active early warning threats.

**Response (200):**
```json
{
  "threats": [
    {
      "id": "uuid",
      "title": "5G Health Misinformation Spike",
      "description": "Multiple similar claims detected...",
      "category": "Health",
      "status": "active",
      "investigation_ids": ["uuid1", "uuid2"],
      "investigation_count": 5,
      "avg_confidence": 0.82,
      "avg_impact": 75.0,
      "first_seen": "2026-02-14T...",
      "last_updated": "2026-02-14T...",
      "escalation_reason": "5 similar claims in 2h, avg impact 75"
    }
  ]
}
```

---

### `GET /threats/stream` (SSE)
Real-time SSE stream for threat alerts. The Early Warning Engine (background task) detects spikes and broadcasts them here.

**SSE Events:**
```
event: threat
data: {"id": "uuid", "title": "...", "category": "Health", ...}

event: ping
data:
```
Keepalive pings every 30 seconds. Use `EventSource` for this one (GET endpoint).

```javascript
const eventSource = new EventSource('http://localhost:8000/threats/stream');
eventSource.addEventListener('threat', (e) => {
  const threat = JSON.parse(e.data);
  // Show alert
});
```

---

## 2. Data Schemas (Response Types)

### InvestigationReport
```typescript
interface InvestigationReport {
  id: string;                              // UUID
  query: string;                           // Original user query
  refined_query: string | null;            // LLM-refined query
  category: "Health" | "Finance" | "Politics" | "Tech" | "General";
  verdict: "TRUE" | "FALSE" | "UNVERIFIED" | "PARTIALLY_TRUE" | "MISLEADING";
  confidence: number;                      // 0.0 - 1.0
  summary: string;                         // Short verdict summary
  detailed_analysis: string;               // Long-form analysis
  evidence: EvidenceItem[];                // All gathered evidence
  cross_reference: CrossReferenceResult | null;
  impact: ImpactScore | null;
  investigation_trail: string[];           // Log of pipeline steps
  created_at: string;                      // ISO timestamp
  user_id: string | null;
  is_published: boolean;
  upvotes: number;
  flags: number;
}
```

### EvidenceItem
```typescript
interface EvidenceItem {
  id: string;                              // UUID
  investigation_id: string;
  source_type: "web_search" | "news" | "authority" | "fact_check";
  source_name: string;                     // e.g., "cancer.gov", "WHO"
  source_url: string | null;
  title: string;
  content: string;                         // Summary of what was found
  credibility_score: number;               // 0.0 - 1.0
  published_date: string | null;
  raw_data: object | null;
}
```

### CrossReferenceResult
```typescript
interface CrossReferenceResult {
  consensus_points: string[];              // Points all sources agree on
  contradictions: string[];                // Conflicting findings
  unique_findings: string[];               // Findings from only one source
  source_agreement_score: number;          // 0.0 - 1.0
  summary: string;
}
```

### ImpactScore
```typescript
interface ImpactScore {
  overall: number;                         // 0 - 100
  topic_sensitivity: ImpactDimension;
  geographic_reach: ImpactDimension;
  emotional_charge: ImpactDimension;
  actionability: ImpactDimension;
  vulnerable_populations: ImpactDimension;
}

interface ImpactDimension {
  score: number;                           // 0 - 100
  explanation: string;
}
```

### AgentStepEvent (SSE data payload)
```typescript
interface AgentStepEvent {
  agent: string;       // "pipeline" | "query_analyzer" | "clarifier" | "web_search" | "news_scanner" | "authority_checker" | "fact_check_lookup" | "cross_reference_analyzer" | "impact_assessor" | "verdict_synthesizer"
  status: string;      // "started" | "completed" | "error"
  message: string;     // Human-readable status
  data: object | null; // Final event has full InvestigationReport here
  timestamp: string;   // ISO timestamp
}
```

### Threat
```typescript
interface Threat {
  id: string;
  title: string;
  description: string;
  category: "Health" | "Finance" | "Politics" | "Tech" | "General";
  status: "active" | "resolved" | "monitoring";
  investigation_ids: string[];
  investigation_count: number;
  avg_confidence: number;
  avg_impact: number;
  first_seen: string;
  last_updated: string;
  escalation_reason: string;
}
```

---

## 3. Enums / Constants

```typescript
type Verdict = "TRUE" | "FALSE" | "UNVERIFIED" | "PARTIALLY_TRUE" | "MISLEADING";
type Category = "Health" | "Finance" | "Politics" | "Tech" | "General";
type ThreatStatus = "active" | "resolved" | "monitoring";
type VoteType = "upvote" | "flag";
type EvidenceType = "web_search" | "news" | "authority" | "fact_check";
type SortOption = "recent" | "impact" | "trending";
```

---

## 4. Investigation Pipeline (How It Works)

The backend runs a 6-agent LangGraph pipeline when you call `/investigate` or `/investigate/sync`:

```
User Query
    │
    ▼
┌──────────────────┐
│  Spam Filter     │ ← LLM-based, rejects spam/abuse (fails open on error)
└──────────────────┘
    │ (pass)
    ▼
┌──────────────────┐
│ 1. Query Analyzer│ ← Refines query, detects category, decides if clarification needed
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ 2. Clarifier     │ ← Generates clarification questions (skipped if not needed)
└──────────────────┘
    │
    ▼
┌──────────────────────────────────────────────┐
│ 3. Evidence Gathering (4 sub-agents, sequential) │
│   • Web Search (Tavily API)                       │
│   • News Scanner (Media Cloud API)                │
│   • Authority Checker (Tavily domain search)      │
│   • Fact-Check Lookup (Google Fact Check API)     │
└──────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│ 4. Cross-Reference       │ ← LLM compares all evidence, finds consensus/contradictions
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│ 5. Impact Assessor       │ ← LLM scores impact across 5 dimensions (0-100 each)
└──────────────────────────┘
    │
    ▼
┌──────────────────────────┐
│ 6. Verdict Synthesizer   │ ← LLM produces final verdict, confidence, summary, analysis
└──────────────────────────┘
    │
    ▼
 Save to Supabase → Return Report
```

**Timing:** ~60 seconds per investigation (rate-limited LLM calls).

---

## 5. Early Warning Engine (Background)

Runs automatically every 2 minutes on the server. It:
1. Fetches investigations from the last 2 hours
2. Clusters them by keyword similarity
3. Detects spikes (≥3 similar claims + avg impact > 60)
4. Creates/updates `Threat` records in Supabase
5. Broadcasts alerts via SSE on `/threats/stream`

---

## 6. Supabase Database Schema

### Tables:
1. **`investigations`** — Stores completed investigation reports
2. **`evidence`** — Individual evidence items (FK → investigations)
3. **`threats`** — Early warning threats
4. **`votes`** — User votes on investigations (upvote/flag)

### Key RLS Policies:
- Published investigations are publicly readable
- Evidence and threats are publicly readable
- Authenticated users can insert investigations and their own votes
- Backend uses service_role key (bypasses RLS)

### Relevant columns for investigations table:
```sql
id UUID PRIMARY KEY,
query TEXT,
refined_query TEXT,
category TEXT CHECK ('Health','Finance','Politics','Tech','General'),
verdict TEXT CHECK ('TRUE','FALSE','UNVERIFIED','PARTIALLY_TRUE','MISLEADING'),
confidence FLOAT (0.0-1.0),
summary TEXT,
detailed_analysis TEXT,
evidence JSONB,
cross_reference JSONB,
impact JSONB,
investigation_trail JSONB,
user_id UUID (FK auth.users),
is_published BOOLEAN,
upvotes INTEGER,
flags INTEGER,
created_at TIMESTAMPTZ
```

---

## 7. Existing Frontend Scaffolding

What already exists in the frontend:

### Tech Stack:
- React 19 + Vite 8
- TailwindCSS v4
- Supabase JS client (`@supabase/supabase-js`)
- React Router v7
- Lucide React icons
- Sonner (toast notifications)
- clsx (utility)

### Existing Files:
- **Auth:** `auth-context.jsx` — Full Supabase auth (signup, login with email/password, Google OAuth, signout)
- **Supabase client:** `lib/supabase.js` — Configured with `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` env vars
- **Protected route:** `protected-route.jsx` — Redirects to `/login` if not authenticated
- **Theme provider:** `theme-provider.jsx` — Dark/light mode toggle
- **UI components:** button, card, input, label, separator, sonner (shadcn/ui style)
- **Pages:** `landing.jsx`, `login.jsx`, `signup.jsx`, `dashboard.jsx` (all placeholder/scaffolded)
- **Navbar:** `navbar.jsx`

### Routes:
```
/           → LandingPage
/login      → LoginPage
/signup     → SignupPage
/dashboard  → DashboardPage (protected, requires auth)
```

### Frontend .env needed:
```
VITE_SUPABASE_URL=https://yrrdgphyzkootbyeirzl.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
VITE_API_URL=http://localhost:8000
```

---

## 8. Suggested Frontend Pages & Features

Based on the backend capabilities, the frontend should include:

### Pages to Build:
1. **Landing Page** — Hero explaining Veritas, CTA to investigate or sign up
2. **Investigation Page** (`/investigate`) — Main page:
   - Text input for claim/query
   - Category selector (optional)
   - Submit button
   - Real-time progress bar showing agent steps (SSE streaming)
   - Full report display when done (verdict badge, confidence, summary, evidence list, impact radar, cross-reference)
3. **Feed Page** (`/feed`) — Public feed of past investigations:
   - Category filter tabs
   - Sort dropdown (recent/impact/trending)
   - Paginated list of investigation cards
   - Click → full report view
4. **Report Detail Page** (`/feed/:id`) — Full investigation report view
5. **Threats Dashboard** (`/threats`) — Early warning:
   - Active threats list
   - Real-time SSE alerts
   - Threat status badges (active/monitoring/resolved)
6. **Dashboard** (`/dashboard`) — User's own investigations and activity

### Key UI Components Needed:
- **VerdictBadge** — Color-coded badge: TRUE=green, FALSE=red, MISLEADING=orange, PARTIALLY_TRUE=yellow, UNVERIFIED=gray
- **ConfidenceMeter** — Circular or bar showing 0-100% confidence
- **ImpactRadar** — Radar/spider chart for the 5 impact dimensions
- **EvidenceCard** — Shows source name, type icon, credibility score, title, content, link
- **InvestigationCard** — Feed card showing query, verdict, confidence, category, upvotes
- **AgentProgressTracker** — Step indicator showing which agents have completed during SSE streaming
- **ThreatAlert** — Alert banner/card for active threats

---

## 9. Example API Response (Real Data)

Here's an actual response from `POST /investigate/sync` with `{"query": "Does 5G cause cancer?"}`:

```json
{
  "id": "54d53ef4-d9ea-4cf2-a2d5-e2c4f7c8a901",
  "query": "Does 5G cause cancer?",
  "refined_query": "What is the scientific evidence regarding the potential link between 5G technology (radiofrequency electromagnetic fields) and cancer risk?",
  "category": "Health",
  "verdict": "FALSE",
  "confidence": 0.85,
  "summary": "Based on the available scientific evidence, the claim that 5G causes cancer is FALSE. Multiple reputable sources, including the WHO, NCI, and NIH, consistently state that there is no established evidence linking 5G or other non-ionizing radiofrequency radiation to cancer.",
  "detailed_analysis": "The investigation involved a comprehensive review of evidence from various sources... [long text]",
  "evidence": [
    {
      "id": "uuid",
      "investigation_id": "uuid",
      "source_type": "web_search",
      "source_name": "canada.ca",
      "source_url": "https://www.canada.ca/...",
      "title": "5G technology, electromagnetic energy and health",
      "content": "Canada.ca discusses 5G technology and health...",
      "credibility_score": 0.8,
      "published_date": null,
      "raw_data": null
    }
    // ... 9 more evidence items
  ],
  "cross_reference": {
    "consensus_points": [
      "5G uses non-ionizing radiation, which does not damage DNA directly.",
      "Current scientific evidence does not establish a causal link between 5G and cancer.",
      "Major health organizations (WHO, NCI, NIH) do not consider 5G a proven carcinogen.",
      "RF radiation from 5G operates within established safety guidelines."
    ],
    "contradictions": [
      "Some sources highlight the IARC classification of RF as 'possibly carcinogenic' (Group 2B), while others emphasize this is precautionary...",
      "One source from the European Parliament suggests a need for further research..."
    ],
    "unique_findings": [],
    "source_agreement_score": 0.75,
    "summary": "The sources largely agree that 5G does not cause cancer..."
  },
  "impact": {
    "overall": 77.0,
    "topic_sensitivity": { "score": 90.0, "explanation": "Health-related claims, especially those involving cancer, are inherently sensitive..." },
    "geographic_reach": { "score": 80.0, "explanation": "5G is a global technology..." },
    "emotional_charge": { "score": 70.0, "explanation": "Cancer fears are deeply emotional..." },
    "actionability": { "score": 85.0, "explanation": "This claim could lead people to avoid 5G..." },
    "vulnerable_populations": { "score": 60.0, "explanation": "While the claim broadly affects the public..." }
  },
  "investigation_trail": [
    "QueryAnalyzer: Refined query, category=Health, no clarification needed",
    "Clarifier: No clarification required — proceeding",
    "WebSearch: Found 5 results",
    "NewsScanner: Error during news scan: ...",
    "AuthorityChecker: Found 5 authority results",
    "FactCheckLookup: No API key configured — skipping fact-check lookup"
  ],
  "created_at": "2026-02-14T...",
  "user_id": null,
  "is_published": true,
  "upvotes": 0,
  "flags": 0
}
```

---

## 10. CORS Configuration

The backend allows CORS from `http://localhost:5173` (the Vite dev server). All methods and headers are allowed. Credentials are enabled.

If the frontend runs on a different port, update `FRONTEND_URL` in the backend `.env`.

---

## 11. Key Implementation Notes

1. **Investigation takes ~60 seconds** — Show a progress UI with agent steps via SSE
2. **SSE for `/investigate`** — Use `fetch` + `ReadableStream` (not `EventSource`, since it's POST)
3. **SSE for `/threats/stream`** — Use `EventSource` (it's GET)
4. **Spam filter runs first** — If rejected, you get a 400 with the reason
5. **`is_published: true`** — All completed investigations are auto-published to the feed
6. **`user_id`** — Currently null (no auth integration with backend yet). Pass the Supabase user UUID if you add auth headers
7. **Voting requires `user_id`** — Pass the authenticated user's UUID from Supabase auth
8. **Categories are optional** — The LLM auto-detects category if not provided
9. **Backend auto-saves** — Investigations and evidence are persisted to Supabase automatically after completion
10. **The feed reads from Supabase** — with `is_published = true` filter, sorted by `created_at`, `impact->overall`, or `upvotes`
