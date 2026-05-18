-- Owner admin dashboard metric snapshots and mirror sync run logs.

CREATE TABLE IF NOT EXISTS public.admin_metric_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_date DATE NOT NULL UNIQUE,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    mrr_pln NUMERIC NOT NULL DEFAULT 0,
    revenue_pln_month NUMERIC NOT NULL DEFAULT 0,
    ai_cost_usd_month NUMERIC NOT NULL DEFAULT 0,
    ai_cost_pln_month NUMERIC NOT NULL DEFAULT 0,
    gross_margin_after_ai_pln NUMERIC NOT NULL DEFAULT 0,
    active_paid_accounts INTEGER NOT NULL DEFAULT 0,
    pending_payment_accounts INTEGER NOT NULL DEFAULT 0,
    active_7d_accounts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_metric_snapshots_date
    ON public.admin_metric_snapshots(snapshot_date DESC);

ALTER TABLE public.admin_metric_snapshots ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.admin_metric_snapshots TO service_role;

CREATE TABLE IF NOT EXISTS public.admin_mirror_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_started_at TIMESTAMPTZ,
    run_finished_at TIMESTAMPTZ,
    ok BOOLEAN NOT NULL DEFAULT FALSE,
    skipped BOOLEAN NOT NULL DEFAULT FALSE,
    reason TEXT NOT NULL DEFAULT '',
    users_count INTEGER NOT NULL DEFAULT 0,
    active_users_count INTEGER NOT NULL DEFAULT 0,
    canceled_users_count INTEGER NOT NULL DEFAULT 0,
    contacts_count INTEGER NOT NULL DEFAULT 0,
    calendar_events_count INTEGER NOT NULL DEFAULT 0,
    errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    calendar_mirror JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_mirror_runs_finished
    ON public.admin_mirror_runs(run_finished_at DESC);

ALTER TABLE public.admin_mirror_runs ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE public.admin_mirror_runs TO service_role;
