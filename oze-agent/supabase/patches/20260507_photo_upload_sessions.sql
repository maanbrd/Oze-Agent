-- Idempotent live patch for active 15-minute Google Drive photo upload sessions.
-- Apply once against the target Supabase database if the table is missing.

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
