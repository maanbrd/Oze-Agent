-- Monotonic Stripe state application and durable delivery deduplication.
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS last_stripe_event_created bigint NOT NULL DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS webhook_log_stripe_event_id_unique
  ON public.webhook_log(stripe_event_id)
  WHERE stripe_event_id IS NOT NULL;
