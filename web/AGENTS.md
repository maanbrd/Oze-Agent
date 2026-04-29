<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Agent-OZE Web Agent Rules

- Read `web/CLAUDE.md`, `../docs/SOURCE_OF_TRUTH.md`, and
  `../docs/CURRENT_STATUS.md` before web changes.
- Use the repo-local Superpowers workflow for multi-phase work.
- Web CRM is read-only: no forms or server actions that mutate clients, notes,
  statuses, meetings, or Calendar event content.
- CRM editing UI must point to Google Sheets/Calendar/Drive or Telegram.
- Phase 1B is rollout/readiness: env, migrations, Stripe sandbox smoke, Google
  OAuth/resource smoke, Telegram pairing smoke, browser smoke.
