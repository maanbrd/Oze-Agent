-- RLS defense-in-depth for Agent-OZE.
-- Cloudflare "SaaS Top 10" audit, mechanism #10 (multi-tenant isolation).
-- Run after supabase_schema.sql + 20260428_web_auth_rls.sql.
--
-- Every sensitive table already has RLS ENABLED but no policy, which Postgres
-- treats as deny-all for anon/authenticated. This migration makes that intent
-- explicit and greppable, regression-tests it (tests/test_rls_defense_in_depth.py,
-- guardrail G4), and hardens it two ways:
--
--   1. FORCE ROW LEVEL SECURITY  -> RLS applies even to the table owner, not
--      just to ordinary roles.
--   2. A RESTRICTIVE deny-all policy -> because restrictive policies are AND-ed,
--      no future *permissive* policy can accidentally re-open these tables; a
--      deliberate decision (dropping this policy) is required to grant access.
--
-- The backend is UNAFFECTED: Supabase's `service_role` has BYPASSRLS and skips
-- all RLS, including FORCE. The web app never reads these tables with the anon
-- key (it uses server-side auth + FastAPI/service_role only), so a pure deny-all
-- is correct here — no own-row SELECT policies are needed. The `users` table is
-- intentionally excluded; it keeps its `users_select_own_profile` SELECT policy.

DO $$
DECLARE
  t TEXT;
  sensitive_tables TEXT[] := ARRAY[
    'promo_codes',
    'beta_access_grants',
    'conversation_history',
    'pending_followups',
    'pending_flows',
    'photo_upload_sessions',
    'interaction_log',
    'user_habits',
    'payment_history',
    'webhook_log',
    'admin_broadcasts',
    'daily_interaction_counts',
    'user_behavior_profiles',
    'user_behavior_profile_runs',
    'offer_templates',
    'offer_seller_profiles',
    'offer_send_attempts'
  ];
BEGIN
  FOREACH t IN ARRAY sensitive_tables LOOP
    EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t);
    EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY;', t);
    EXECUTE format('DROP POLICY IF EXISTS %I ON public.%I;', t || '_deny_anon_authenticated', t);
    EXECUTE format(
      'CREATE POLICY %I ON public.%I '
      'AS RESTRICTIVE FOR ALL TO anon, authenticated '
      'USING (false) WITH CHECK (false);',
      t || '_deny_anon_authenticated', t
    );
  END LOOP;
END $$;
