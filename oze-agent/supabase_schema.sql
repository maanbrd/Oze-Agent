-- OZE-Agent Supabase Schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query → Run)
-- All 11 tables, indexes, and RLS policies

-- ============================================================
-- TABLES
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    phone TEXT,
    address TEXT,
    age INTEGER,
    products JSONB DEFAULT '[]',
    referral_source TEXT,
    google_access_token TEXT,
    google_refresh_token TEXT,
    google_token_expiry TIMESTAMPTZ,
    google_sheets_id TEXT,
    google_sheets_name TEXT,
    google_calendar_id TEXT,
    google_calendar_name TEXT,
    google_drive_folder_id TEXT,
    onboarding_survey JSONB DEFAULT '{}',
    morning_brief_hour INTEGER DEFAULT 7,
    reminder_minutes_before INTEGER DEFAULT 60,
    default_meeting_duration INTEGER DEFAULT 60,
    working_days JSONB DEFAULT '[1,2,3,4,5]',
    pipeline_statuses JSONB DEFAULT '["Nowy lead","Spotkanie umówione","Spotkanie odbyte","Oferta wysłana","Podpisane","Zamontowana","Rezygnacja z umowy","Nieaktywny","Odrzucone"]',
    sheet_columns JSONB,
    subscription_status TEXT DEFAULT 'pending_payment',
    subscription_plan TEXT,
    subscription_expires_at TIMESTAMPTZ,
    subscription_current_period_end TIMESTAMPTZ,
    activation_paid BOOLEAN DEFAULT FALSE,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    stripe_checkout_session_id TEXT,
    promo_code_used TEXT,
    consent_terms BOOLEAN DEFAULT FALSE,
    consent_marketing BOOLEAN DEFAULT FALSE,
    consent_phone_contact BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    telegram_link_code TEXT,
    telegram_link_code_expires TIMESTAMPTZ,
    is_admin BOOLEAN DEFAULT FALSE,
    is_suspended BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    last_morning_brief_sent_date DATE
);

CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    value REAL,
    max_uses INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pending_followups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    event_id TEXT NOT NULL,
    event_title TEXT NOT NULL,
    event_end_time TIMESTAMPTZ NOT NULL,
    follow_up_time TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending',
    asked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE pending_flows (
    telegram_id BIGINT PRIMARY KEY,
    flow_type TEXT NOT NULL,
    flow_data JSONB NOT NULL,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE interaction_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL,
    interaction_type TEXT,
    model_used TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost_usd REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_habits (
    telegram_id BIGINT PRIMARY KEY,
    default_meeting_duration INTEGER DEFAULT 60,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payment_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    amount_pln REAL NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    przelewy24_order_id TEXT UNIQUE,
    stripe_event_id TEXT UNIQUE,
    stripe_checkout_session_id TEXT,
    stripe_invoice_id TEXT,
    stripe_subscription_id TEXT,
    stripe_customer_id TEXT,
    currency TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE webhook_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    payload JSONB NOT NULL,
    stripe_event_id TEXT UNIQUE,
    stripe_event_type TEXT,
    processed BOOLEAN DEFAULT FALSE,
    duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE TABLE billing_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    stripe_event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE TABLE admin_broadcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message TEXT NOT NULL,
    target TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    sent_by UUID REFERENCES users(id)
);

CREATE TABLE daily_interaction_counts (
    telegram_id BIGINT NOT NULL,
    date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    borrowed_from_tomorrow INTEGER DEFAULT 0,
    PRIMARY KEY (telegram_id, date)
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_stripe_customer_id ON users(stripe_customer_id) WHERE stripe_customer_id IS NOT NULL;
CREATE INDEX idx_users_stripe_subscription_id ON users(stripe_subscription_id) WHERE stripe_subscription_id IS NOT NULL;
CREATE INDEX idx_conversation_history_telegram_id ON conversation_history(telegram_id, created_at DESC);
CREATE INDEX idx_interaction_log_telegram_id ON interaction_log(telegram_id, created_at DESC);
CREATE INDEX idx_pending_followups_status ON pending_followups(status, event_end_time);
CREATE INDEX idx_daily_counts_date ON daily_interaction_counts(telegram_id, date);
CREATE INDEX idx_webhook_log_source ON webhook_log(source, created_at DESC);
CREATE INDEX idx_admin_broadcasts_status ON admin_broadcasts(status);

-- ============================================================
-- ROW LEVEL SECURITY
-- Service key has full access (bypasses RLS).
-- Anon key is blocked from all sensitive tables.
-- ============================================================

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE promo_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_followups ENABLE ROW LEVEL SECURITY;
ALTER TABLE pending_flows ENABLE ROW LEVEL SECURITY;
ALTER TABLE interaction_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE billing_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_broadcasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_interaction_counts ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- MIGRATIONS (for existing deployments)
-- Run only the ALTER blocks relevant to your current schema version.
-- ============================================================

-- Phase 6A (morning brief dedup): adds last_morning_brief_sent_date and
-- a partial index to efficiently enumerate eligible users.
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS last_morning_brief_sent_date DATE;

CREATE INDEX IF NOT EXISTS idx_users_eligible_brief
    ON users (is_suspended, is_deleted, telegram_id)
    WHERE is_suspended = FALSE AND is_deleted = FALSE AND telegram_id IS NOT NULL;
