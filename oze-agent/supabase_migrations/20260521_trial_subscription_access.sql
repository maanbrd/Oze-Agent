-- Stripe trial access: keep access active through the trial period and record
-- whether Stripe will cancel the subscription at period end.

ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS subscription_cancel_at_period_end BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_users_trial_subscription_access
  ON public.users(subscription_status, stripe_livemode, subscription_current_period_end)
  WHERE subscription_status = 'trialing';
