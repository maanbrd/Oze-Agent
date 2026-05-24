# Railway scheduled jobs — marketing daily loop (Phase 0.18)

Maan sets these up in Railway dashboard → project `oze-agent` → **+ New** →
**Empty Service** → Settings → **Cron Schedule**. Each cron runs as a fresh
container in its own service and references the same env vars as the `bot`
service. Set each cron service root directory to `/oze-agent`; the start
commands below assume that working directory.

> **Timezone:** Railway crons run in **UTC**. Times below are pinned to the
> UTC equivalent of **Warsaw winter time** (UTC+1). Result: each spring
> they shift 1h later in Warsaw local time (e.g. `06:00 Warsaw → 07:00 Warsaw`).
> Accept this 1h DST drift or update twice a year. Long-term fix: configure
> Railway `TZ=Europe/Warsaw` env var if the platform supports it on cron
> services (check Railway docs at provisioning time).

## Cron entries

| Job | Cron (UTC) | Warsaw (winter) | Warsaw (summer) | Command |
|---|---|---|---|---|
| `marketing-generate-daily` | `0 5 * * *` | 06:00 | 07:00 | `python -m scripts.marketing.generate_daily` |
| `marketing-iterate-feedback` | `0 6 * * *` | 07:00 | 08:00 | `python -m scripts.marketing.iterate_from_feedback` |
| `marketing-publish-morning` | `30 6 * * *` | 07:30 | 08:30 | `python -m scripts.marketing.auto_publish --min-approved 2` |
| `marketing-digest` | `0 7 * * *` | 08:00 | 09:00 | `python -m scripts.marketing.morning_digest` |
| `marketing-queue-alert` | `0 16 * * *` | 17:00 | 18:00 | `python -m scripts.marketing.queue_depth_alert` |
| `marketing-publish-evening` | `0 18 * * *` | 19:00 | 20:00 | `python -m scripts.marketing.auto_publish --min-approved 2` |

## Required env vars (reference from the `bot` service)

All cron services need references to these vars from the `bot` service:

- `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`
- `META_APP_ID` + `META_APP_SECRET` + `META_FB_PAGE_TOKEN` + `META_FB_PAGE_ID` + `META_IG_BUSINESS_ID`
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `ENCRYPTION_KEY` (for decrypting per-user Google OAuth tokens)

## Validation after first deploy

For each cron, after the first scheduled fire, check Railway logs:

| Job | Expected log on success | Expected log on no-op |
|---|---|---|
| `marketing-generate-daily` | `generate_daily: DONE — row N = <campaign_id>` | `generate_daily: chosen type = X (not wired in MVP)` |
| `marketing-iterate-feedback` | `iterate_from_feedback: processed N row(s)` | `iterate_from_feedback: found 0 row(s)` |
| `auto-publish-*` | `auto_publish: PUBLISHED <campaign_id>` (or similar from publish_single flow) | `auto_publish: skipped — APPROVED queue depth=N < min=2` |
| `marketing-digest` | `morning_digest: sent to telegram_id=<id>` | (always sends, even if empty) |
| `marketing-queue-alert` | `queue_depth_alert: notification sent` | `queue_depth_alert: queue healthy, no notification sent` |

## Manual catch-up commands

Each script supports `--dry-run` to test without writing. Examples:

```bash
# Test generate (picks type, scenario; no Drive/Sheet write)
railway run --service bot --environment production python \
    -m scripts.marketing.generate_daily --dry-run

# Force a specific type (skip round-robin)
railway run --service bot --environment production python \
    -m scripts.marketing.generate_daily --force-type D-AGENT

# Process feedback now (e.g. between cron windows)
railway run --service bot --environment production python \
    -m scripts.marketing.iterate_from_feedback

# Publish ignoring the time-window check (manual catch-up)
railway run --service bot --environment production python \
    -m scripts.marketing.auto_publish --force-now --min-approved 1

# Send digest right now
railway run --service bot --environment production python \
    -m scripts.marketing.morning_digest
```

## DST handover schedule

Mark these dates in Maan's calendar to either accept the 1h shift or
re-pin cron times:

- **Last Sunday of March** (clocks forward, summer time starts)
- **Last Sunday of October** (clocks back, winter time)

If 1h drift is unacceptable, edit each cron's UTC time at those handovers.
