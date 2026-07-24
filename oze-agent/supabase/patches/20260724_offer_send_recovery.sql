-- Durable identity and safe recovery for confirmed Gmail sends.
ALTER TABLE public.offer_send_attempts
  ADD COLUMN IF NOT EXISTS client_ref jsonb;

ALTER TABLE public.offer_send_attempts
  DROP CONSTRAINT IF EXISTS offer_send_attempts_status_check;
ALTER TABLE public.offer_send_attempts
  ADD CONSTRAINT offer_send_attempts_status_check
  CHECK (status IN ('pending', 'sending', 'sent', 'failed', 'reconcile_required'));

CREATE INDEX IF NOT EXISTS idx_offer_send_attempts_stale_sending
  ON public.offer_send_attempts(locked_at)
  WHERE status = 'sending';
