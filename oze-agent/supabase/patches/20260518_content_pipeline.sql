-- Content-analysis pipeline tables for marketing sub-agent (Hormozi-style workflow).
-- Phase 0 uses content_assets, content_scores, icp_avatars, ad_variants directly via
-- Claude Code skills (oze-creative-scorer, oze-icp-avatars, oze-ad-generator).
-- content_metrics fills in from Phase 2 onward (Meta Ads / IG Graph / Hyros).
--
-- Idempotent — safe to re-run.
-- Plan: ~/.claude/plans/to-czym-b-dziemy-si-lucky-forest.md
-- Market context: project_market_context_2026 memory.

-- 1) content_assets — annotated videos / posts / ads (own or reference) used to train rubric
CREATE TABLE IF NOT EXISTS public.content_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source TEXT NOT NULL CHECK (source IN (
        'youtube', 'instagram', 'facebook', 'tiktok', 'linkedin', 'meta_ad_library', 'manual'
    )),
    source_url TEXT NOT NULL UNIQUE,
    asset_kind TEXT NOT NULL CHECK (asset_kind IN (
        'reel', 'feed', 'tiktok', 'youtube_short', 'youtube_long', 'meta_ad', 'linkedin_post', 'other'
    )),
    training_set TEXT CHECK (training_set IN (
        'A_category_creating', 'B_ai_for_sales', 'C_pl_niche_b2b', 'D_oze_voice_anchor', 'own', NULL
    )),
    is_own BOOLEAN NOT NULL DEFAULT FALSE,
    category TEXT,
    title TEXT,
    uploader TEXT,
    duration_seconds NUMERIC,
    raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    transcript TEXT,
    on_screen_text_first_5s TEXT[],
    frames_dir TEXT,
    annotation JSONB,
    subjective_perf TEXT CHECK (subjective_perf IN ('win', 'mid', 'flop', NULL)),
    notes TEXT,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_assets_training_set
    ON public.content_assets(training_set) WHERE training_set IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_content_assets_subjective_perf
    ON public.content_assets(subjective_perf) WHERE subjective_perf IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_content_assets_is_own
    ON public.content_assets(is_own) WHERE is_own = TRUE;

ALTER TABLE public.content_assets ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.content_assets TO service_role;

-- 2) content_metrics — objective performance signals (Phase 2+); long-format for any metric type
CREATE TABLE IF NOT EXISTS public.content_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES public.content_assets(id) ON DELETE CASCADE,
    metric_type TEXT NOT NULL CHECK (metric_type IN (
        'views', 'saves', 'shares', 'comments', 'followers_delta',
        'cpc', 'cpm', 'ctr', 'roas', 'cpa', 'spend',
        'manual_score'
    )),
    value NUMERIC NOT NULL,
    source TEXT CHECK (source IN (
        'meta_ads_api', 'ig_graph', 'fb_graph', 'tiktok_api', 'hyros', 'manual', 'estimated'
    )),
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_metrics_asset_type
    ON public.content_metrics(asset_id, metric_type);

ALTER TABLE public.content_metrics ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.content_metrics TO service_role;

-- 3) content_scores — rubric scores per dimension (produced by oze-creative-scorer skill)
CREATE TABLE IF NOT EXISTS public.content_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES public.content_assets(id) ON DELETE CASCADE,
    scorer_version TEXT NOT NULL,
    dimension TEXT NOT NULL,
    score NUMERIC NOT NULL CHECK (score >= 0 AND score <= 10),
    rationale TEXT,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_content_scores_asset_dim
    ON public.content_scores(asset_id, dimension);
CREATE INDEX IF NOT EXISTS idx_content_scores_version
    ON public.content_scores(scorer_version);

ALTER TABLE public.content_scores ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.content_scores TO service_role;

-- 4) icp_avatars — 3 (Phase 0) personas of OZE handlowiec with adaptation mindset 2026
CREATE TABLE IF NOT EXISTS public.icp_avatars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    deal_breakers JSONB NOT NULL DEFAULT '[]'::jsonb,
    buying_triggers JSONB NOT NULL DEFAULT '[]'::jsonb,
    scam_detector JSONB NOT NULL DEFAULT '[]'::jsonb,
    channels_present JSONB NOT NULL DEFAULT '[]'::jsonb,
    voice_examples JSONB NOT NULL DEFAULT '[]'::jsonb,
    adaptation_pain_2026 JSONB NOT NULL DEFAULT '[]'::jsonb,
    professionalism_anchor TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    avatar_version TEXT NOT NULL DEFAULT 'v0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_icp_avatars_active
    ON public.icp_avatars(active) WHERE active = TRUE;

ALTER TABLE public.icp_avatars ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.icp_avatars TO service_role;

-- 5) ad_variants — generated 10×3 batches; tracks lifecycle from draft → deployed → measured
CREATE TABLE IF NOT EXISTS public.ad_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    angle TEXT NOT NULL,
    source_winner_id UUID REFERENCES public.content_assets(id),
    hook TEXT NOT NULL,
    body TEXT NOT NULL,
    cta TEXT,
    generated_by_skill_version TEXT NOT NULL,
    predicted_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    avatar_responses JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'shortlisted', 'deployed', 'archived', 'paused'
    )),
    deployed_to TEXT CHECK (deployed_to IN (
        'meta_ads', 'organic_ig', 'organic_fb', 'organic_yt', 'organic_tiktok', 'organic_linkedin', NULL
    )),
    actual_metrics JSONB,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_variants_status
    ON public.ad_variants(status);
CREATE INDEX IF NOT EXISTS idx_ad_variants_source_winner
    ON public.ad_variants(source_winner_id) WHERE source_winner_id IS NOT NULL;

ALTER TABLE public.ad_variants ENABLE ROW LEVEL SECURITY;
GRANT ALL ON TABLE public.ad_variants TO service_role;
