@AGENTS.md

# Agent-OZE Web App — rules

Pełne reguły UI/UX są w `docs/WEB_APP_BRIEF_FOR_CLAUDE_DESIGN.md`. Lokalnie
obowiązują twarde zasady:

1. **UI po polsku.** Każdy user-facing tekst po polsku, bez korpomowy ("Świetnie!", "Z przyjemnością!", "Oto..."). Code/comments po angielsku.
2. **Dashboard/app dark-mode first.** Tło `--background: #0b0d10`, foreground `--foreground: #e4e4e7`, akcent `--accent: #16a34a`. Light mode opcjonalny w przyszłości — projektujemy najpierw dark.
3. **Brak czatu z agentem w MVP.** Web app to przegląd, planowanie, ustawienia, płatności. Rozmowa z agentem dzieje się **wyłącznie w Telegramie**. Nie dodawaj komponentów typu chat input, message list, conversation view.
4. **Telegram pozostaje miejscem mutacji CRM.** R1 z `agent_behavior_spec_v5.md` (confirmation before write) działa po stronie bota. Web app **nie wykonuje mutacji** danych klientów (add_client, change_status, add_note, add_meeting).
5. **Wyjątek: generator ofert.** `/oferty` zapisuje systemowe dane generatora
   (szablony ofert, profil sprzedawcy, logo, treść emaila) i generuje testowy
   PDF. Nie wysyła ofert klientom i nie edytuje Sheets bezpośrednio.
6. **Widoki klientów pozostają read-only.** Czytamy z Google Sheets/Calendar/Drive
   (ich source of truth). Side panel klienta — read-only, deep link do Sheets
   jako jedyna akcja "edycyjna".

Wyjątek: konfiguracja own konta (profil, ustawienia, płatności) — to operacje na danych usera, nie klientach.

---

Implementation guardrails (G1-G7) z głównego planu obowiązują, gdy będą wprowadzane Supabase/Stripe/Google integration:
- G1: `SUPABASE_SERVICE_KEY` server-only (`import "server-only"` w `lib/supabase/admin.ts`)
- G2: `/internal/google-token` z HMAC + allowlist + no-log + timeout + audit log + refresh-stays-Railway
- G3: Stripe webhook idempotent + outbox + reconciler
- G4: RLS testy zielone przed dashboardem
- G5: `<DataFreshnessBadge>` "ostatnio odświeżone X min temu" obok danych z Sheets
- G6: company extension to osobny milestone
- G7: ujawnione sekrety → rotacja, log w `docs/SECRETS_AUDIT.md`
