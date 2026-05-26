-- Durable Telegram offer-send queue fields.
ALTER TABLE public.offer_send_attempts
    ADD COLUMN IF NOT EXISTS queued_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS attempt_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS lock_owner TEXT,
    ADD COLUMN IF NOT EXISTS telegram_result_sent_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS command_text TEXT;

CREATE INDEX IF NOT EXISTS idx_offer_send_attempts_queue_due
    ON public.offer_send_attempts(status, next_attempt_at, created_at)
    WHERE status = 'pending';
