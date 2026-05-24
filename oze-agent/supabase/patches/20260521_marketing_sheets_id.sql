-- Add marketing_sheets_id to users table for marketing queue Sheet.
--
-- Single-owner column (Maan / OZE_OWNER_USER_ID) — points at the Agent-OZE
-- marketing review queue spreadsheet bootstrapped via
-- `scripts/content_factory/bootstrap_marketing_sheet.py`.
--
-- Idempotent — safe to re-run.

ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS marketing_sheets_id TEXT;

COMMENT ON COLUMN public.users.marketing_sheets_id IS
    'Spreadsheet ID for Agent OZE marketing review queue (single-owner: Maan).';
