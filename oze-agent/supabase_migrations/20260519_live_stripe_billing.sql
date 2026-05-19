-- Live Stripe billing hardening: distinguish live payments from sandbox tests
-- and persist the paid subscription period used by access gates.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS stripe_livemode BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMPTZ;

ALTER TABLE public.payment_history
  ADD COLUMN IF NOT EXISTS stripe_livemode BOOLEAN DEFAULT FALSE;

ALTER TABLE public.webhook_log
  ADD COLUMN IF NOT EXISTS stripe_livemode BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_users_live_subscription_access
  ON public.users(subscription_status, stripe_livemode, subscription_current_period_end)
  WHERE activation_paid IS TRUE;
