-- Phase 0C billing baseline: Stripe sandbox + onboarding payment state.
-- Run after 20260428_web_auth_rls.sql.

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

ALTER TABLE public.webhook_log
  ADD COLUMN IF NOT EXISTS stripe_event_id TEXT,
  ADD COLUMN IF NOT EXISTS stripe_event_type TEXT,
  ADD COLUMN IF NOT EXISTS processed_at TIMESTAMPTZ;

CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_log_stripe_event_id
  ON public.webhook_log(stripe_event_id)
  WHERE stripe_event_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.billing_outbox (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.users(id),
  stripe_event_id TEXT UNIQUE NOT NULL,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  processed BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

ALTER TABLE public.billing_outbox ENABLE ROW LEVEL SECURITY;

-- Refresh the auth trigger so registration survey metadata lands in public.users.
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  display_name TEXT;
  survey JSONB;
BEGIN
  display_name := NULLIF(
    TRIM(
      COALESCE(NEW.raw_user_meta_data->>'name', '') || ' ' ||
      COALESCE(NEW.raw_user_meta_data->>'first_name', '') || ' ' ||
      COALESCE(NEW.raw_user_meta_data->>'last_name', '')
    ),
    ''
  );

  survey := COALESCE(NEW.raw_user_meta_data->'onboarding_survey', '{}'::jsonb);

  INSERT INTO public.users (
    auth_user_id,
    email,
    name,
    phone,
    referral_source,
    onboarding_survey,
    consent_terms,
    consent_marketing,
    consent_phone_contact
  )
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(display_name, SPLIT_PART(NEW.email, '@', 1), 'Użytkownik'),
    NULLIF(NEW.raw_user_meta_data->>'phone', ''),
    NULLIF(COALESCE(survey->>'referral_source', NEW.raw_user_meta_data->>'referral_source'), ''),
    survey,
    COALESCE((NEW.raw_user_meta_data->>'consent_terms')::BOOLEAN, FALSE),
    COALESCE((NEW.raw_user_meta_data->>'consent_marketing')::BOOLEAN, FALSE),
    COALESCE((NEW.raw_user_meta_data->>'consent_phone_contact')::BOOLEAN, FALSE)
  )
  ON CONFLICT (email) DO UPDATE
    SET auth_user_id = COALESCE(public.users.auth_user_id, EXCLUDED.auth_user_id),
        name = COALESCE(NULLIF(public.users.name, ''), EXCLUDED.name),
        phone = COALESCE(NULLIF(public.users.phone, ''), EXCLUDED.phone),
        referral_source = COALESCE(public.users.referral_source, EXCLUDED.referral_source),
        onboarding_survey = CASE
          WHEN public.users.onboarding_survey IS NULL
            OR public.users.onboarding_survey = '{}'::jsonb
          THEN EXCLUDED.onboarding_survey
          ELSE public.users.onboarding_survey
        END,
        updated_at = NOW()
    WHERE public.users.auth_user_id IS NULL
       OR public.users.auth_user_id = EXCLUDED.auth_user_id;

  RETURN NEW;
END;
$$;
