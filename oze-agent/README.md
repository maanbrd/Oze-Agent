# OZE-Agent

AI-powered sales assistant for B2C renewable energy salespeople in Poland.

- **Bot:** Telegram (@OZEAgentBot) — voice, text, photos
- **API:** FastAPI backend (Railway)
- **Dashboard:** Next.js web app (`web/`, Vercel `oze-agent.vercel.app`)

Current web branch: `feat/web-phase-0c` / PR #5. Phase 0C/0D/0E/0F/Phase 1 is
code-complete on the branch: Stripe sandbox boundary, onboarding, read-only CRM
pages, Google OAuth/resource setup, Telegram pairing, and account-only settings.
Next stage is rollout/readiness smoke, not live mode.

## Known Constraints

- **Python 3.13 required.** Python 3.14+ not yet supported due to python-telegram-bot asyncio incompatibility. Before upgrading Python, verify python-telegram-bot changelog for 3.14 support.
