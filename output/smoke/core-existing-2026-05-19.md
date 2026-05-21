# OZE-Agent E2E Report 🛑

_Generated: 2026-05-19T19:10:47.539660+00:00_

**Overall:** BLOCKER
**Scenarios:** 7 (pass 2, blocker 3)

**Check tag counts:** ✅ pass=17, ⚠️ known_drift=2, 🟡 expected_fail=0, ❌ fail=3, 🛑 blocker=3

## 🛑 Blockers

## 🛑 `add_client_dup_dopisac_update_path` — BLOCKER  _[mutating_core]_

- started: `2026-05-19T19:08:46.003406+00:00`
- ended:   `2026-05-19T19:09:16.517110+00:00` (30.5s)

| Check | Tag | Detail |
|---|---|---|
| `setup_save_confirmed` | 🛑 `blocker` | setup save reply lacks confirm marker; got ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spr'] |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-210846-B11'
new_email: 'updated-e2e-beta-tester-210846-b11@example.pl'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-210846-B11, E2E-Beta-City, 600100200, PV'
```
</details>

## 🛑 `r7_next_action_prompt_after_add_client` — BLOCKER  _[rules]_

- started: `2026-05-19T19:09:32.339554+00:00`
- ended:   `2026-05-19T19:10:12.555364+00:00` (40.2s)

| Check | Tag | Detail |
|---|---|---|
| `setup_save_confirmed` | 🛑 `blocker` | add_client save unconfirmed; got ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spr'] |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-210932-T04'
add_trigger: 'dodaj klienta E2E-Beta-Tester-210932-T04, E2E-Beta-City, 600100200, PV'
```
</details>

## 🛑 `r6_active_client_implicit_reference` — BLOCKER  _[rules]_

- started: `2026-05-19T19:10:17.057733+00:00`
- ended:   `2026-05-19T19:10:47.536235+00:00` (30.5s)

| Check | Tag | Detail |
|---|---|---|
| `setup_save_confirmed` | 🛑 `blocker` | setup save reply lacks confirm marker; got ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spr'] |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-211017-T03'
note_content: 'zainteresowany pompą ciepła'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-211017-T03, E2E-Beta-City, 600100200, PV'
```
</details>

---

## ❌ Fails

## ❌ `add_meeting_phone_call_save` — FAIL  _[mutating_core]_

- started: `2026-05-19T19:06:43.601571+00:00`
- ended:   `2026-05-19T19:08:00.305093+00:00` (76.7s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-210643-B07' setup OK |
| `got_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `three_button_mutation_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |
| `no_internal_field_leak` | ✅ `pass` | no internal fields leaked |
| `card_has_phone_icon` | ⚠️ `known_drift` | icon=None, header='✅ Dodać telefon?' — _ref: INTENCJE_MVP.md §4 — phone-call card uses 📞 icon_ |
| `card_mentions_meeting_date` | ✅ `pass` | expected '21.05.2026' (PL) or its ISO form in card; got: '✅ Dodać telefon?\n\n• Klient: E2E-Beta-Tester-210643-B07\n• Data: 21.05.2026 (czwartek)\n• Godzina: 10:00\n• Czas trwania: 15 min\n• Miejsce: telefonicznie' |
| `pl_date_format` | ✅ `pass` | PL date format OK |
| `save_button_present` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ❌ `fail` | got 1 reply(ies); first: '⚠️ Google Calendar jest chwilowo niedostępny. Spotkanie NIE zostało dodane. Spróbuj ponownie za kilka minut.' |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-210643-B07'
expected_pl_date: '21.05.2026 (Czwartek)'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-210643-B07, E2E-Beta-City, 600100200, PV'
setup_co_dalej_closed: True
trigger: 'zadzwonię 21.05.2026 o 10:00 do E2E-Beta-Tester-210643-B07, E2E-Beta-City'
reply_count: 1
save_label: '✅ Zapisać'
confirm_replies: ['⚠️ Google Calendar jest chwilowo niedostępny. Spotkanie NIE zostało dodane. Spróbuj ponownie za kilka minut.']
save_confirmed_replies: ['⚠️ Google Calendar jest chwilowo niedostępny. Spotkanie NIE zostało dodane. Spróbuj ponownie za kilka minut.']
save_confirmed_co_dalej_closed: False
```
</details>

## ❌ `show_client_multi_match_disambig` — FAIL  _[read_only]_

- started: `2026-05-19T19:09:21.020972+00:00`
- ended:   `2026-05-19T19:09:27.837051+00:00` (6.8s)

| Check | Tag | Detail |
|---|---|---|
| `offers_disambig` | ❌ `fail` | expected disambig prompt or ≥2 button options; got: 'Nie mam "Jan Kowalski" w bazie.' |
| `lists_warszawa_match` | ❌ `fail` | expected 'Warszawa' marker; got: 'Nie mam "Jan Kowalski" w bazie.' |
| `no_mutation_buttons` | ✅ `pass` | buttons=[] |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |

<details><summary>Context</summary>

```
trigger: 'pokaż Jana Kowalskiego'
fixture_dependency: 'Run mcp__oze-e2e__e2e_seed_fixtures before this scenario. Two E2E-Beta-Fixture-Jan-Kowalski rows must exist (Warszawa + Kraków).'
reply_count: 1
reply_text: 'Nie mam "Jan Kowalski" w bazie.'
reply_buttons: []
```
</details>

---

## ⚠️ Known drifts (PASS but log)

## ✅ `cancel_one_click_no_loop` — PASS  _[rules]_

- started: `2026-05-19T19:08:04.807533+00:00`
- ended:   `2026-05-19T19:08:31.121044+00:00` (26.3s)

| Check | Tag | Detail |
|---|---|---|
| `got_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `cancel_button_present` | ✅ `pass` | ❌ Anulować |
| `one_click_no_loop` | ⚠️ `known_drift` | card edited in-place, no follow-up question — _ref: agent_behavior_spec_v5.md §2.R1 expects '🫡 Anulowane.' line_ |

<details><summary>Context</summary>

```
trigger: 'dodaj klienta E2E-Beta-Tester-210804-R1-cancel, E2E-Beta-City, 600100200'
cancel_replies: []
cancel_reply_count: 0
```
</details>

---

## ✅ Clean PASS

## ✅ `show_day_plan_tomorrow` — PASS  _[read_only]_

- started: `2026-05-19T19:08:35.622626+00:00`
- ended:   `2026-05-19T19:08:41.500800+00:00` (5.9s)

| Check | Tag | Detail |
|---|---|---|
| `show_day_plan_no_buttons` | ✅ `pass` | no buttons (read-only) |
| `dates_in_pl_format` | ✅ `pass` | PL date format OK |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |
| `no_internal_field_leak` | ✅ `pass` | no internal fields leaked |
| `reply_is_tomorrow_plan_or_empty` | ✅ `pass` | expected '20.05.2026' or 'Na jutro' or empty marker; got: 'Na 20.05.2026 (środa) nic nie masz w kalendarzu.' |

<details><summary>Context</summary>

```
expected_pl_date: '20.05.2026 (Środa)'
trigger: 'co mam jutro?'
reply_count: 1
reply_text: 'Na 20.05.2026 (środa) nic nie masz w kalendarzu.'
```
</details>

---
