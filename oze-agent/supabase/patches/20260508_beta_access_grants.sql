-- Beta access grants for onboarding without Stripe payment.
-- Insert lowercase emails manually, for example:
-- INSERT INTO beta_access_grants (email, note) VALUES ('tester@example.pl', 'May beta');

CREATE TABLE IF NOT EXISTS beta_access_grants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked')),
    auth_user_id UUID,
    claimed_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT beta_access_grants_email_lowercase CHECK (email = lower(email))
);

CREATE INDEX IF NOT EXISTS idx_beta_access_grants_auth_user_id
    ON beta_access_grants(auth_user_id);

CREATE INDEX IF NOT EXISTS idx_beta_access_grants_status
    ON beta_access_grants(status);

ALTER TABLE beta_access_grants ENABLE ROW LEVEL SECURITY;
