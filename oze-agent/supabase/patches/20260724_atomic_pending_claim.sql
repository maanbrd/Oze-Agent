-- Serialize Telegram mutation callbacks across processes.
ALTER TABLE public.pending_flows
  ADD COLUMN IF NOT EXISTS processing_token uuid,
  ADD COLUMN IF NOT EXISTS processing_started_at timestamptz;

CREATE OR REPLACE FUNCTION public.claim_pending_flow(
  p_telegram_id bigint,
  p_expected_updated_at timestamptz DEFAULT NULL
)
RETURNS SETOF public.pending_flows
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
  UPDATE public.pending_flows
     SET processing_token = gen_random_uuid(),
         processing_started_at = now()
   WHERE telegram_id = p_telegram_id
     AND (p_expected_updated_at IS NULL OR updated_at = p_expected_updated_at)
     AND (
       processing_token IS NULL
       OR processing_started_at < now() - interval '15 minutes'
     )
  RETURNING *;
$$;

REVOKE ALL ON FUNCTION public.claim_pending_flow(bigint, timestamptz) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.claim_pending_flow(bigint, timestamptz) TO service_role;
