@AGENTS.md

# Agent-OZE Web App — rules (Phase 1)

Stan na 29.04.2026: Phase 0C/0D/0E/0F/Phase 1 są code-complete na
`feat/web-phase-0c` / PR #5. Następny etap to Phase 1B rollout/readiness, czyli
realne env + sandbox smoke, nie nowe copy ani marketing polish.

W web app obowiązują twarde zasady:

1. **UI po polsku.** Każdy user-facing tekst po polsku, bez korpomowy ("Świetnie!", "Z przyjemnością!", "Oto..."). Code/comments po angielsku.
2. **Dashboard/app dark-mode first.** Tło `--background: #0b0d10`, foreground `--foreground: #e4e4e7`, akcent `--accent: #16a34a`. Light mode opcjonalny w przyszłości — projektujemy najpierw dark.
3. **Brak czatu z agentem w MVP.** Web app to przegląd, planowanie, ustawienia, płatności. Rozmowa z agentem dzieje się **wyłącznie w Telegramie**. Nie dodawaj komponentów typu chat input, message list, conversation view.
4. **Telegram pozostaje miejscem mutacji.** R1 z `agent_behavior_spec_v5.md` (confirmation before write) działa po stronie bota. Web app **nie wykonuje mutacji** danych klientów (add_client, change_status, add_note, add_meeting).
5. **Web app jest read-only dla CRM.** Czytamy z Google Sheets/Calendar/Drive przez FastAPI/adapters. Side panel klienta — read-only, deep link do Sheets/Calendar/Drive jako jedyna akcja "edycyjna".

Wyjątek: konfiguracja own konta (profil, ustawienia, płatności) — to operacje na danych usera, nie klientach.

---

Implementation guardrails (G1-G7) z głównego planu obowiązują, gdy będą wprowadzane Supabase/Stripe/Google integration:
- G1: `SUPABASE_SERVICE_KEY` server-only (`import "server-only"` w `lib/supabase/admin.ts`)
- G2: `/internal/google-token` z HMAC + allowlist + no-log + timeout + audit log + refresh-stays-Railway
- G3: Payment webhook idempotent + outbox + reconciler (provider decision lives in backend/env docs)
- G4: RLS testy zielone przed dashboardem
- G5: `<DataFreshnessBadge>` "ostatnio odświeżone X min temu" obok danych z Sheets
- G6: company extension to osobny milestone
- G7: ujawnione sekrety → rotacja, log w `docs/SECRETS_AUDIT.md`

Phase 0B auth boundary:
- Next.js może używać Supabase tylko do Auth/session cookies przez publishable/anon key.
- Dashboard/business data idą przez FastAPI po `Authorization: Bearer <Supabase JWT>`.
- FastAPI waliduje Supabase JWT przez JWKS, z legacy `SUPABASE_JWT_SECRET` tylko jako fallback dla HS256.
- RLS chroni browser access, ale FastAPI używa service key, więc każdy endpoint musi autoryzować po JWT subject.

Phase 0C/1 boundaries:
- Stripe = hosted Checkout. Next.js tworzy Checkout i weryfikuje webhook, ale trwałe billing writes robi FastAPI przez HMAC.
- Stop on `livemode: true` until Maan explicitly approves production billing.
- Onboarding = FastAPI `/api/onboarding/*`; Next.js wysyła Supabase access token.
- Google OAuth state is signed by backend; nie ufaj publicznemu `user_id` z URL.
- CRM data path = `lib/crm/adapters.ts` -> FastAPI `/api/dashboard/crm` -> Google Sheets/Calendar.
- Completed users must see `live` or `unavailable`; silent demo fallback is only for unauth/incomplete users.
- Before marking ready, run `npm run test:invariants && npm run lint && npm run build`.
