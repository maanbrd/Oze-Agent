-- Idempotent live patch for post-MVP app tables used by photo and offer smoke tests.
-- Safe to run more than once against the target Supabase database.

CREATE TABLE IF NOT EXISTS public.photo_upload_sessions (
    telegram_id BIGINT PRIMARY KEY,
    user_id UUID REFERENCES public.users(id),
    client_row INTEGER NOT NULL,
    folder_id TEXT NOT NULL,
    folder_link TEXT NOT NULL,
    display_label TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_photo_upload_sessions_expires
    ON public.photo_upload_sessions(expires_at);

ALTER TABLE public.photo_upload_sessions ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS public.offer_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
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

CREATE TABLE IF NOT EXISTS public.offer_seller_profiles (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
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

CREATE TABLE IF NOT EXISTS public.offer_send_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key TEXT UNIQUE NOT NULL,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    telegram_id BIGINT,
    client_row INTEGER,
    client_name TEXT,
    client_city TEXT,
    recipients JSONB DEFAULT '[]',
    invalid_recipients JSONB DEFAULT '[]',
    offer_template_id UUID REFERENCES public.offer_templates(id) ON DELETE SET NULL,
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
    ON public.offer_templates(user_id, status, sort_order);

CREATE INDEX IF NOT EXISTS idx_offer_send_attempts_user_created
    ON public.offer_send_attempts(user_id, created_at DESC);

ALTER TABLE public.offer_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.offer_seller_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.offer_send_attempts ENABLE ROW LEVEL SECURITY;

INSERT INTO storage.buckets (id, name, "public", file_size_limit, allowed_mime_types)
VALUES (
    'offer-logos',
    'offer-logos',
    FALSE,
    2097152,
    ARRAY['image/png', 'image/jpeg', 'image/webp']
)
ON CONFLICT (id) DO UPDATE SET
    "public" = EXCLUDED."public",
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

GRANT ALL ON TABLE public.photo_upload_sessions TO service_role;
GRANT ALL ON TABLE public.offer_templates TO service_role;
GRANT ALL ON TABLE public.offer_seller_profiles TO service_role;
GRANT ALL ON TABLE public.offer_send_attempts TO service_role;

NOTIFY pgrst, 'reload schema';
