-- Web Auth function hardening for Agent-OZE.
-- Run after 20260428_web_auth_rls.sql.
--
-- The auth trigger still executes this SECURITY DEFINER function internally,
-- but browser/API roles must not be able to call it directly through RPC.

REVOKE ALL ON FUNCTION public.handle_new_auth_user() FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.handle_new_auth_user() FROM anon;
REVOKE EXECUTE ON FUNCTION public.handle_new_auth_user() FROM authenticated;
