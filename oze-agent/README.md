# OZE-Agent

AI-powered sales assistant for B2C renewable energy salespeople in Poland.

- **Bot:** Telegram (@OZEAgentBot) — voice, text, photos
- **API:** FastAPI backend (Railway)
- **Dashboard:** Next.js (oze-agent.pl)
- **Offer generator:** `/oferty` in the web app + FastAPI offers routes +
  `shared/offers/` for templates, pricing, PDF, email rendering and Gmail send

## Known Constraints

- **Python 3.13 required.** Python 3.14+ not yet supported due to python-telegram-bot asyncio incompatibility. Before upgrading Python, verify python-telegram-bot changelog for 3.14 support.
