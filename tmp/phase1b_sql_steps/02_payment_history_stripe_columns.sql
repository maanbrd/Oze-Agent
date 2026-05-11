ALTER TABLE public.payment_history
  ADD COLUMN IF NOT EXISTS stripe_event_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_checkout_session_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_invoice_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
  ADD COLUMN IF NOT EXISTS currency TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_payment_history_stripe_event_id
  ON public.payment_history(stripe_event_id)
  WHERE stripe_event_id IS NOT NULL;
