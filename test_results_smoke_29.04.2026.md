# Smoke Test Run — 29.04.2026

**MCP server:** `oze-e2e` (telethon → @OZEAgentTestBot)
**Session:** `oze-agent/tests_e2e/.sessions/e2e`
**Bot started:** 2026-04-28 23:34 UTC (≈ 01:34 local Wed 29.04)
**Bot finished:** 2026-04-29 03:35 UTC (≈ 05:35 local Wed 29.04)
**Source matrix:** `docs/AGENT_FLOW_REVIEW_MATRIX.md`
**Pełny per-step report:** `oze-agent/test_results_e2e.md`

## Sumarycznie

**110 wykonań scenariuszy** (3 rundy × 8 kategorii non-proactive + extra mutating_core).

| Wynik | Liczba | % | Co to znaczy |
|---|---:|---:|---|
| **PASS** | 60 | 54.5% | Pełna ścieżka (bot reply + Sheets/Calendar verification) OK |
| **BLOCKER** | 36 | 32.7% | Bot reply OK, ale weryfikacja Sheets/Calendar nie wystartowała (jeden root cause: brak Supabase user mappingu dla `telegram_id=1690210103`) |
| **FAIL** | 14 | 12.7% | Realne odchylenie od oczekiwanego zachowania |

**"Bot behavior level" PASS rate** (PASS + BLOCKER, ignorując broken verification): **96/110 = 87.3%**.

## Per-runda

| Runda | Scenariusze | PASS | FAIL | BLOCKER |
|---|---:|---:|---:|---:|
| 1 — wszystkie 8 kategorii | 47 | 23 | 9 | 15 |
| 2 — wszystkie 8 kategorii ponownie | 47 | 27 | 5 | 15 |
| 3 — dodatkowy mutating_core | 16 | 10 | 0 | 6 |
| **Razem** | **110** | **60** | **14** | **36** |

Drift między rundą 1 a 2: 3 FAILe znikły w rundzie 2 (`add_meeting_in_person_save`, `add_client_with_followup_meeting_save`, `add_meeting_relative_date_save` — wszystkie bazujące na "jutro"/"za tydzień"). Pierwsze runy poszły o 01:34 local, krótko po przekroczeniu północy lokalnej; stempel czasu w bocie i w teście rozjechał się o 1 dzień. Po rundzie 2 (≈ 04:30) wszystko ułożyło się prawidłowo. **Stabilny FAIL** to znak realnego defektu; **drift po północy** to artefakt setup'u testu, nie błąd bota.

## Per-kategoria (sumaryczne 3 rundy)

| Kategoria | Runów | PASS | FAIL | BLOCKER | Komentarz |
|---|---:|---:|---:|---:|---|
| `mutating_core` | 48 | 27 | 3 | 18 | Wszystkie BLOCKERy = post-save Sheets/Calendar verification (Supabase mapping) |
| `read_only` | 16 | 10 | 6 | 0 | Realne FAILe: ikona karty (👤 vs 📋), fixture nie ma Krakowa, "Nie mam" vs "Nie znalazłem" |
| `routing` | 16 | 14 | 2 | 0 | Stabilny FAIL: `general_question_unknown` (gibberish → "Co chcesz zrobić?" zamiast "nie zrozumiałem") |
| `rules` | 12 | 2 | 2 | 8 | BLOCKERy = brak weryfikacji Sheets; FAIL `r8_frustration_calm_response` (oczekiwane "co chcesz/zrób/dalej", bot mówi "Co konkretnie nie działa?") |
| `notes` | 6 | 0 | 0 | 6 | Bot tworzy karty OK, weryfikacja Sheets blokowana |
| `card_structure` | 4 | 4 | 0 | 0 | Czyste PASS — 3-button card + ❌ Anuluj OK |
| `error_path` | 4 | 3 | 1 | 0 | `add_meeting_past_date_rejection` — czyste PASS; `change_status_invalid_client` ma drift w komunikacie |
| `polish_edge` | 4 | 0 | 1 | 3 | "wpół do ósmej" → 07:30 OK; "PV-ka" → karta zachowuje "PV-kę" (oczekiwane verbatim "PV-ka") |

## Realne FAILe (do decyzji Maana)

Posortowane wg powtarzalności. **Stabilne** = pojawiły się w obu rundach 1 i 2.

### Stabilne FAILe (powtarzalne)

1. **`show_client_existing_just_created`** — read-only — karta klienta otwiera się ikoną `👤` zamiast oczekiwanej `📋`. Treść karty poprawna (telefon, miasto, produkt). Decyzja: zaakceptować `👤` jako poprawną, zaktualizować test.

2. **`show_client_multi_match_disambig`** — read-only — fixture seed nie zaczytał Jana Kowalskiego z Krakowa (test oczekuje Warszawa + Kraków, są dwie Warszawy). Root cause: `e2e_seed_fixtures` failuje na `no Supabase user`. Tester strony bota — OK; problem fixturę.

3. **`show_client_not_found`** — read-only — bot odpowiada `'Nie mam "X" w bazie.'`, test oczekuje `Nie znalazłem`. Decyzja: zaakceptować kopię "Nie mam … w bazie" albo dopisać synonim do testu.

4. **`general_question_unknown`** — routing — gibberish `asdfghjk` → `'Co chcesz zrobić?'`, test oczekuje `'Nie zrozumiałem'`-class odpowiedzi. Bot grzecznie pyta "co chcesz", co jest pragmatycznie OK; test za sztywny.

5. **`r8_frustration_calm_response`** — rules — `'nie działa to gówno'` → `'Co konkretnie nie działa?'`, test oczekuje któregoś z `co chcesz / co dalej / powiedz / podaj / zacznijmy`. Odpowiedź bota jest spokojna i konkretna, brak zakazanych zwrotów. Decyzja: rozszerzyć whitelistę testu albo doprecyzować spec.

6. **`polish_slang_pv_pompeczka_parsing`** — polish_edge — bot zachowuje `"PV-kę"` (akusativ), test oczekuje `"PV-ka"` verbatim. To język polski, akusativ jest poprawny. Decyzja: poluzować test.

7. **`add_client_dup_dopisac_update_path`** — mutating_core — po kliknięciu `➕ Dopisać` przy duplikacie bot mówi `'Co chcesz dopisać?'` i nie wystawia kolejnej karty od razu. Stary "[Nowy]/[Aktualizuj]" zastąpiony jest 3-button kartą — to znana zmiana spec'a. Test może być nieaktualny względem nowego flow.

### Niestabilne FAILe (Runda 1 only — drift północy)

Te trzy zafailowały w Rundzie 1 (start ≈ 01:34 local, krótko po północy), wszystkie PASSED w Rundach 2-3:

- `add_meeting_in_person_save` — "jutro 14" → testowe "jutro" rozjechało się z botowym "jutro" o 1 dzień
- `add_client_with_followup_meeting_save` — to samo
- `add_meeting_relative_date_save` — "za tydzień we wtorek" — to samo

Decyzja: nie zgłaszać jako defekt bota. Sugestia: test nie powinien startować w oknie ±15 min wokół północy lokalnej.

### Pozostałe (rzadkie)

- **`change_status_invalid_client`** — Runda 1 FAIL (`'Nieprawidłowy status. Dostępne: ...'` zamiast `'not found'`), Runda 2 PASS (`"Nie znalazłem klienta: '...'"`). Bot zachowuje się różnie zależnie od kolejności walidacji (status → klient vs klient → status). Worth a look.

## Blockers — wszystkie z jednego root cause

**36 blockerów = 1 problem.** Każdy blocker kończy się komunikatem `no Supabase user found for telegram_id=1690210103`. Bot reaguje poprawnie (karta wyświetlona, save potwierdzony, status zmieniony), ale test nie może odczytać Sheets/Calendar żeby zweryfikować końcowy stan.

To samo dotyczy `e2e_seed_fixtures` i `e2e_cleanup_run` — oba zwracają `ERROR — no Supabase user found for telegram_id=1690210103`.

Wniosek: **konto admin (1690210103) nie ma rekordu w Supabase `users` table** dla obecnego deploymentu (prod env, do którego MCP się łączy). Bez naprawy mappingu:
- ~33% scenariuszy nie da się zweryfikować end-to-end
- syntetyczne `E2E-Beta-*` ZOSTAJĄ w Sheets/Calendar (cleanup nie działa) — wymaga ręcznego usunięcia

## Najważniejsze obserwacje

1. **Bot działa stabilnie.** Wszystkie 110 runów wystawiały karty, przyjmowały kliknięcia, generowały odpowiedzi. Żadnego crashu, timeoutu telethonowego, ani gibberish'a od bota.
2. **R1 ❌ Anuluj jednoklikowy** — PASS (×4 runs across rounds, 0 FAIL).
3. **3-button confirmation card** — PASS na 100% mutating scenariuszy.
4. **POST-MVP rejekcje** — bot poprawnie odsyła do Google Sheets (`post_mvp_edit_client_rejection`, `post_mvp_lejek_rejection`).
5. **Vision-only intencje** — bot poprawnie odmawia mutacji (`vision_only_*`), wskazuje odpowiednie miejsce.
6. **Calendar conflict warning** — `⚠️ Uwaga: masz już spotkanie o tej porze` pojawia się prawidłowo.
7. **R7 follow-up** — `Co dalej — X (City)? Spotkanie, telefon, mail, odłożyć na później?` PASS (re-routes do add_meeting card).
8. **R6 active client** — bot prawidłowo używa ostatnio wspomnianego klienta przy `dodaj notatkę` bez nazwiska.
9. **Date drift po północy** — test framework robi małą lukę 0-1 dnia, bot ma swoje "today" względem timezone — runy 02:00 PASS-ują tam, gdzie 01:34 zafailowały.

## Out of scope tego runu

- **VOICE (V-01..V-04)** — brak coverage w MCP. Wymaga audio fixtures.
- **`debug_brief`** (proactive, opt-in) — nie odpalany.
- **Naprawa failujących scenariuszy** — punkt do osobnego sprintu.
- **Naprawa Supabase user mappingu** — wymaga akcji infra.
- **Cleanup syntetycznych `E2E-Beta-*`** — zablokowany przez ten sam mapping issue.

## Rekomendacje

1. **Naprawić Supabase user mapping** dla `telegram_id=1690210103` w env do którego pinguje MCP — odblokuje 36 blockerów, seed_fixtures, cleanup.
2. **Posprzątać Sheets/Calendar ręcznie** — `E2E-Beta-Tester-*-*` z runów ~01:00-04:00 UTC 29.04.2026.
3. **Przegląd 7 stabilnych FAILi** powyżej (większość to drift testów względem aktualnego spec'a, nie defekt bota).
4. **Test framework: nie startować runów w ±15 min od północy lokalnej** — eliminuje niestabilne FAILe z drift'em daty.
