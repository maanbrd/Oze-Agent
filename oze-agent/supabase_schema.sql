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
    morning_brief_hour INTEGER DEFAULT 7,
    reminder_minutes_before INTEGER DEFAULT 60,
    default_meeting_duration INTEGER DEFAULT 60,
    working_days JSONB DEFAULT '[1,2,3,4,5]',
    pipeline_statuses JSONB DEFAULT '["Nowy lead","Spotkanie umówione","Spotkanie odbyte","Oferta wysłana","Podpisane","Zamontowana","Rezygnacja z umowy","Nieaktywny","Odrzucone"]',
    sheet_columns JSONB,
    subscription_status TEXT DEFAULT 'pending_payment',
    subscription_plan TEXT,
    subscription_expires_at TIMESTAMPTZ,
    activation_paid BOOLEAN DEFAULT FALSE,
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

CREATE TABLE photo_upload_sessions (
    telegram_id BIGINT PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    client_row INTEGER NOT NULL,
    folder_id TEXT NOT NULL,
    folder_link TEXT NOT NULL,
    display_label TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
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
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE webhook_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL,
    payload JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
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

CREATE TABLE offer_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready')),
    product_type TEXT,
    price_net_pln INTEGER,
    vat_rate INTEGER CHECK (vat_rate IN (8, 23)),
    subsidy_amount_pln INTEGER,
    pv_power_kwp NUMERIC,
    storage_capacity_kwh NUMERIC,
    panel_brand TEXT,
    panel_model TEXT,
    inverter_brand TEXT,
    inverter_model TEXT,
    storage_brand TEXT,
    storage_model TEXT,
    construction TEXT,
    protections_ac_dc TEXT,
    installation TEXT,
    monitoring_ems TEXT,
    warranty TEXT,
    payment_terms TEXT,
    implementation_time TEXT,
    validity TEXT,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE offer_seller_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company_name TEXT,
    logo_path TEXT,
    accent_color TEXT,
    email_signature TEXT,
    email_body_template TEXT,
    seller_name TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE offer_send_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    client_row INTEGER,
    client_name TEXT,
    client_city TEXT,
    recipients JSONB DEFAULT '[]',
    invalid_recipients JSONB DEFAULT '[]',
    offer_template_id UUID REFERENCES offer_templates(id) ON DELETE SET NULL,
    offer_template_name TEXT,
    offer_number INTEGER,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'sent', 'failed')),
    gmail_message_id TEXT,
    error TEXT,
    sent_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_conversation_history_telegram_id ON conversation_history(telegram_id, created_at DESC);
CREATE INDEX idx_interaction_log_telegram_id ON interaction_log(telegram_id, created_at DESC);
CREATE INDEX idx_pending_followups_status ON pending_followups(status, event_end_time);
CREATE INDEX idx_photo_upload_sessions_expires ON photo_upload_sessions(expires_at);
CREATE INDEX idx_daily_counts_date ON daily_interaction_counts(telegram_id, date);
CREATE INDEX idx_webhook_log_source ON webhook_log(source, created_at DESC);
CREATE INDEX idx_admin_broadcasts_status ON admin_broadcasts(status);
CREATE INDEX idx_offer_templates_user_status_order ON offer_templates(user_id, status, sort_order);
CREATE INDEX idx_offer_send_attempts_user_created ON offer_send_attempts(user_id, created_at DESC);

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
ALTER TABLE photo_upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interaction_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_habits ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_broadcasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_interaction_counts ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_seller_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_send_attempts ENABLE ROW LEVEL SECURITY;

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

-- Photo upload sessions (active 15-minute Drive target).
CREATE TABLE IF NOT EXISTS photo_upload_sessions (
    telegram_id BIGINT PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    client_row INTEGER NOT NULL,
    folder_id TEXT NOT NULL,
    folder_link TEXT NOT NULL,
    display_label TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_photo_upload_sessions_expires
    ON photo_upload_sessions(expires_at);

ALTER TABLE photo_upload_sessions ENABLE ROW LEVEL SECURITY;

-- Offer generator (templates, profile, 90-day technical send log).
CREATE TABLE IF NOT EXISTS offer_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'ready')),
    product_type TEXT,
    price_net_pln INTEGER,
    vat_rate INTEGER CHECK (vat_rate IN (8, 23)),
    subsidy_amount_pln INTEGER,
    pv_power_kwp NUMERIC,
    storage_capacity_kwh NUMERIC,
    panel_brand TEXT,
    panel_model TEXT,
    inverter_brand TEXT,
    inverter_model TEXT,
    storage_brand TEXT,
    storage_model TEXT,
    construction TEXT,
    protections_ac_dc TEXT,
    installation TEXT,
    monitoring_ems TEXT,
    warranty TEXT,
    payment_terms TEXT,
    implementation_time TEXT,
    validity TEXT,
    sort_order INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offer_seller_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company_name TEXT,
    logo_path TEXT,
    accent_color TEXT,
    email_signature TEXT,
    email_body_template TEXT,
    seller_name TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offer_send_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    client_row INTEGER,
    client_name TEXT,
    client_city TEXT,
    recipients JSONB DEFAULT '[]',
    invalid_recipients JSONB DEFAULT '[]',
    offer_template_id UUID REFERENCES offer_templates(id) ON DELETE SET NULL,
    offer_template_name TEXT,
    offer_number INTEGER,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'sending', 'sent', 'failed')),
    gmail_message_id TEXT,
    error TEXT,
    sent_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_offer_templates_user_status_order
    ON offer_templates(user_id, status, sort_order);

CREATE INDEX IF NOT EXISTS idx_offer_send_attempts_user_created
    ON offer_send_attempts(user_id, created_at DESC);

ALTER TABLE offer_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_seller_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_send_attempts ENABLE ROW LEVEL SECURITY;

INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'offer-logos',
    'offer-logos',
    FALSE,
    2097152,
    ARRAY['image/png', 'image/jpeg', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;
