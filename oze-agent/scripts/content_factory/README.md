# content_factory/

Skrypt do generowania carouseli marketingowych Agent-OZE.

**Skill source of truth:** `~/.agents/skills/oze-content-factory/SKILL.md`
**Plan:** `~/.claude/plans/to-czym-b-dziemy-si-lucky-forest.md`

## Quick start

1. **Z `oze-agent/` directory:**

   ```bash
   cd /Users/mansoniasty/workflows/Agent-OZE/oze-agent
   railway run --service bot --environment production \
     python -m scripts.content_factory.generate_carousel \
     --config /tmp/my-carousel.json
   ```

2. **Dry run (validate only, no API calls):**

   ```bash
   railway run --service bot --environment production \
     python -m scripts.content_factory.generate_carousel \
     --config /tmp/my-carousel.json \
     --dry-run
   ```

3. **Skip Drive upload (local only):**

   ```bash
   railway run --service bot --environment production \
     python -m scripts.content_factory.generate_carousel \
     --config /tmp/my-carousel.json \
     --skip-drive
   ```

## Required env

- `OPENAI_API_KEY` — from `bot.config.Config` (auto-loaded via Railway env)

## Optional env

- `OZE_OWNER_USER_ID` — Maan's Supabase user UUID; required for Drive upload. Without it script saves locally only.

## JSON config

See `~/.agents/skills/oze-content-factory/examples/carousel_config_example.json` for full schema.

Minimum required keys:
- `campaign_id` (string, used as folder name)
- `typ` (one of A/B/C/D)
- `concept` (concept slug from concept-library.md)
- `language` (must be "pl")
- `slides` (list; each has `n`, `copy`, `visual_prompt`, `is_cta`)

## Output

- Local: `~/marketing-output/<campaign_id>/slide_NN.png` + `brand_agent_oze_icon.png` + `brand_agent_oze_logo.png` + `meta.json`
- Drive (if `OZE_OWNER_USER_ID` set): `Agent-OZE/Marketing/<campaign_id>/` + `drive.json` saved locally with folder URL

## Brand-lock

Canonical brand assets:
- `assets/brand/agent-oze-icon.png`
- `assets/brand/agent-oze-logo.png`

The generator copies both assets into every campaign output folder and includes them in Drive uploads. Use these files for CTA slides, thumbnails, brand bars, and post-processing. Do not regenerate or invent the Agent OZE logo.

Every visual_prompt is prefixed with brand-lock instructions before being sent to gpt-image-2:
- Solid `#0b0d10` background
- `#3DFF7A` accent
- No people / AI characters / futuristic
- Monoline icons only, system sans-serif typography
- Official mark: glowing green ring + centered green dot on near-black

See `oze-agent/scripts/content_factory/generate_carousel.py` `BRAND_LOCK_PREFIX` constant or `~/.agents/skills/oze-content-factory/references/openai_image_prompt_template.md` for full prefix.

## Validation

Script auto-checks before generation:
- All required JSON keys
- `language == "pl"`
- `typ` in A/B/C/D
- Banned anglicyzmy in copy (storage, follow-up, retrofit, leady, growth hack, AI rewolucja)
- At least one slide with `is_cta: true`

Warnings printed; fatal errors (missing keys / no slides) abort.

## Drive upload flow

Uses `shared/google_drive.py::get_drive_service(user_id)` — same OAuth pattern as photo uploads. Creates folders `Agent-OZE/Marketing/<campaign_id>/` if not exists, uploads all PNG + `meta.json`.

For first run: ensure Maan's user record in Supabase `users` table has valid `google_refresh_token` (already true if Maan has connected Google in webapp).
