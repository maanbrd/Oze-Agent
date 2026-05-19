-- Admin-only user behavior profile agent.
-- Source of truth stays in Supabase system data; CRM data stays in Google.

CREATE TABLE IF NOT EXISTS user_behavior_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    profile_markdown TEXT NOT NULL DEFAULT '',
    insights_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_analyzed_message_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'ok', 'skipped', 'failed')),
    error TEXT,
    model TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    analyzed_messages_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_behavior_profile_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ok', 'skipped', 'failed')),
    profile_markdown TEXT,
    insights_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    analyzed_from TIMESTAMPTZ,
    analyzed_to TIMESTAMPTZ,
    messages_count INTEGER DEFAULT 0,
    error TEXT,
    model TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_behavior_profiles_last_run
    ON user_behavior_profiles(last_run_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_behavior_profile_runs_user_created
    ON user_behavior_profile_runs(user_id, created_at DESC);

ALTER TABLE user_behavior_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_behavior_profile_runs ENABLE ROW LEVEL SECURITY;
