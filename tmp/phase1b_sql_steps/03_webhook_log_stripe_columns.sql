ALTER TABLE public.webhook_log
  ADD COLUMN IF NOT EXISTS stripe_event_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_event_type TEXT,
  ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_log_stripe_event_id
  ON public.webhook_log(stripe_event_id)
  WHERE stripe_event_id IS NOT NULL;
