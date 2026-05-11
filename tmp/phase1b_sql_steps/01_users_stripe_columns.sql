ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS onboarding_survey JSONB DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_checkout_session_id TEXT,
  ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id
  ON public.users(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_stripe_subscription_id
  ON public.users(stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;
