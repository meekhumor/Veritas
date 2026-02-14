-- ============================================================================
-- Veritas — Supabase Database Schema
-- Run this in the Supabase SQL Editor to create all required tables.
-- ============================================================================

-- ── Investigations ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    refined_query TEXT,
    category TEXT NOT NULL DEFAULT 'General'
        CHECK (category IN ('Health', 'Finance', 'Politics', 'Tech', 'General')),
    verdict TEXT NOT NULL DEFAULT 'UNVERIFIED'
        CHECK (verdict IN ('TRUE', 'FALSE', 'UNVERIFIED', 'PARTIALLY_TRUE', 'MISLEADING')),
    confidence FLOAT NOT NULL DEFAULT 0.0
        CHECK (confidence >= 0.0 AND confidence <= 1.0),
    summary TEXT NOT NULL DEFAULT '',
    detailed_analysis TEXT NOT NULL DEFAULT '',
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    cross_reference JSONB,
    impact JSONB,
    investigation_trail JSONB NOT NULL DEFAULT '[]'::jsonb,
    user_id UUID REFERENCES auth.users(id),
    is_published BOOLEAN NOT NULL DEFAULT false,
    upvotes INTEGER NOT NULL DEFAULT 0,
    flags INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_investigations_published ON investigations (is_published, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_investigations_category ON investigations (category);
CREATE INDEX IF NOT EXISTS idx_investigations_verdict ON investigations (verdict);
CREATE INDEX IF NOT EXISTS idx_investigations_user ON investigations (user_id);
CREATE INDEX IF NOT EXISTS idx_investigations_created ON investigations (created_at DESC);

-- ── Evidence ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL
        CHECK (source_type IN ('web_search', 'news', 'authority', 'fact_check')),
    source_name TEXT NOT NULL,
    source_url TEXT,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    credibility_score FLOAT NOT NULL DEFAULT 0.5
        CHECK (credibility_score >= 0.0 AND credibility_score <= 1.0),
    published_date TEXT,
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_evidence_investigation ON evidence (investigation_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source_type ON evidence (source_type);

-- ── Threats (Early Warning) ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS threats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'General'
        CHECK (category IN ('Health', 'Finance', 'Politics', 'Tech', 'General')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'resolved', 'monitoring')),
    investigation_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    investigation_count INTEGER NOT NULL DEFAULT 0,
    avg_confidence FLOAT NOT NULL DEFAULT 0.0,
    avg_impact FLOAT NOT NULL DEFAULT 0.0,
    first_seen TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT now(),
    escalation_reason TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_threats_status ON threats (status);
CREATE INDEX IF NOT EXISTS idx_threats_updated ON threats (last_updated DESC);

-- ── Votes ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    vote_type TEXT NOT NULL CHECK (vote_type IN ('upvote', 'flag')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (investigation_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_votes_investigation ON votes (investigation_id);
CREATE INDEX IF NOT EXISTS idx_votes_user ON votes (user_id);

-- ── Row Level Security (RLS) ─────────────────────────────────────────────

-- Investigations: public read for published, authenticated write
ALTER TABLE investigations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can read published investigations"
    ON investigations FOR SELECT
    USING (is_published = true);

CREATE POLICY "Authenticated users can insert investigations"
    ON investigations FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Users can update their own investigations"
    ON investigations FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

-- Service role bypasses RLS for backend operations
CREATE POLICY "Service role full access to investigations"
    ON investigations FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Evidence: read-only for public, service role manages
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can read evidence"
    ON evidence FOR SELECT
    USING (true);

CREATE POLICY "Service role full access to evidence"
    ON evidence FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Threats: public read, service role manages
ALTER TABLE threats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can read threats"
    ON threats FOR SELECT
    USING (true);

CREATE POLICY "Service role full access to threats"
    ON threats FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Votes: users manage their own votes
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read their own votes"
    ON votes FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own votes"
    ON votes FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Service role full access to votes"
    ON votes FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
