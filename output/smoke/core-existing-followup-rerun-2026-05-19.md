# OZE-Agent E2E Report ❌

_Generated: 2026-05-19T20:16:04.643700+00:00_

**Overall:** FAIL
**Scenarios:** 5 (pass 3, blocker 0)

**Check tag counts:** ✅ pass=33, ⚠️ known_drift=1, 🟡 expected_fail=0, ❌ fail=3, 🛑 blocker=0

## ❌ Fails

## ❌ `add_client_dup_dopisac_update_path` — FAIL  _[mutating_core]_

- started: `2026-05-19T20:11:58.791974+00:00`
- ended:   `2026-05-19T20:13:06.473230+00:00` (67.7s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-221158-B11' setup OK |
| `setup_sheets_row_ready` | ✅ `pass` | row 72 matched |
| `setup_sheets_row_ready_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `got_dup_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `duplicate_update_card_detected` | ❌ `fail` | card text: '📋 E2E-Beta-Tester-221158-B11, E2E-Beta-City\nPV\nTel. 600 100 200\nEmail: updated-e2e-beta-tester-221158-b11@example.pl\n❓ Brakuje: Adres, Źródło pozyskania\nZapisać / dopisać / anulować?' |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-221158-B11'
new_email: 'updated-e2e-beta-tester-221158-b11@example.pl'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-221158-B11, E2E-Beta-City, 600100200, PV'
setup_co_dalej_closed: True
dup_trigger: 'dodaj klienta E2E-Beta-Tester-221158-B11, E2E-Beta-City, 600100200, PV, updated-e2e-beta-tester-221158-b11@example.pl'
reply_count: 1
```
</details>

## ❌ `show_client_multi_match_disambig` — FAIL  _[read_only]_

- started: `2026-05-19T20:13:10.977704+00:00`
- ended:   `2026-05-19T20:13:15.564719+00:00` (4.6s)

| Check | Tag | Detail |
|---|---|---|
| `offers_disambig` | ❌ `fail` | expected disambig prompt or ≥2 button options; got: '⚠️ Anulowane.' |
| `lists_warszawa_match` | ❌ `fail` | expected 'Warszawa' marker; got: '⚠️ Anulowane.' |
| `no_mutation_buttons` | ✅ `pass` | buttons=[] |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |

<details><summary>Context</summary>

```
trigger: 'pokaż Jana Kowalskiego'
fixture_dependency: 'Run mcp__oze-e2e__e2e_seed_fixtures before this scenario. Two E2E-Beta-Fixture-Jan-Kowalski rows must exist (Warszawa + Kraków).'
reply_count: 1
reply_text: '⚠️ Anulowane.'
reply_buttons: []
```
</details>

---

## ⚠️ Known drifts (PASS but log)

## ✅ `add_meeting_phone_call_save` — PASS  _[mutating_core]_

- started: `2026-05-19T20:10:40.092120+00:00`
- ended:   `2026-05-19T20:11:54.287261+00:00` (74.2s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-221040-B07' setup OK |
| `got_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `three_button_mutation_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |
| `no_internal_field_leak` | ✅ `pass` | no internal fields leaked |
| `card_has_phone_icon` | ⚠️ `known_drift` | icon=None, header='✅ Dodać telefon?' — _ref: INTENCJE_MVP.md §4 — phone-call card uses 📞 icon_ |
| `card_mentions_meeting_date` | ✅ `pass` | expected '21.05.2026' (PL) or its ISO form in card; got: '✅ Dodać telefon?\n\n• Klient: E2E-Beta-Tester-221040-B07\n• Data: 21.05.2026 (czwartek)\n• Godzina: 10:00\n• Czas trwania: 15 min\n• Miejsce: telefonicznie' |
| `pl_date_format` | ✅ `pass` | PL date format OK |
| `save_button_present` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Telefon dodany do kalendarza.' |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-221040-B07'
expected_pl_date: '21.05.2026 (Czwartek)'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-221040-B07, E2E-Beta-City, 600100200, PV'
setup_co_dalej_closed: True
trigger: 'zadzwonię 21.05.2026 o 10:00 do E2E-Beta-Tester-221040-B07, E2E-Beta-City'
reply_count: 1
save_label: '✅ Zapisać'
confirm_replies: ['✅ Telefon dodany do kalendarza.']
save_confirmed_co_dalej_closed: False
```
</details>

---

## ✅ Clean PASS

## ✅ `r7_next_action_prompt_after_add_client` — PASS  _[rules]_

- started: `2026-05-19T20:13:20.069167+00:00`
- ended:   `2026-05-19T20:14:41.638970+00:00` (81.6s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_committed` | ✅ `pass` | client E2E-Beta-Tester-221320-T04 created |
| `bot_emitted_co_dalej_prompt` | ✅ `pass` | R7 needs the 'Co dalej' prompt; replies: ['✅ Zapisane.', 'Co dalej — E2E-Beta-Tester-221320-T04 (E2E-Beta-City)? Spotkanie, telefon, mail, odłożyć na później?'] |
| `got_meeting_card_via_r7` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_card_references_client` | ✅ `pass` | expected 'E2E-Beta-Tester-221320-T04'; got: '✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-221320-T04\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: E2E-Beta-City\n• Status: Nowy lead → Spotkanie umówione\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Bet' |
| `meeting_card_has_14_00` | ✅ `pass` | expected '14:00'; got: '✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-221320-T04\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: E2E-Beta-City\n• Status: Nowy lead → Spotkanie umówione\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Bet' |
| `meeting_save_button_present` | ✅ `pass` | ✅ Zapisać |
| `meeting_saved` | ✅ `pass` | got 1 reply(ies); first: '✅ Spotkanie dodane do kalendarza. Status klienta: Spotkanie umówione.' |
| `calendar_event_created` | ✅ `pass` | event id='snpiods92vv5uo548hdt8s7cuk' title='Spotkanie — E2E-Beta-Tester-221320-T04' |
| `calendar_event_created_start_time` | ✅ `pass` | event start='2026-05-20T14:00:00+02:00' matches expected '2026-05-20T14:00:00+02:00' (diff 0.0 min) |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-221320-T04'
add_trigger: 'dodaj klienta E2E-Beta-Tester-221320-T04, E2E-Beta-City, 600100200, PV'
next_action_trigger: 'spotkanie jutro o 14:00'
meeting_reply_count: 1
meeting_saved_co_dalej_closed: False
```
</details>

## ✅ `r6_active_client_implicit_reference` — PASS  _[rules]_

- started: `2026-05-19T20:14:46.143698+00:00`
- ended:   `2026-05-19T20:16:04.641720+00:00` (78.5s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-221446-T03' setup OK |
| `got_note_card_via_active_client` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `card_references_active_client_name` | ✅ `pass` | R6 should put active client 'E2E-Beta-Tester-221446-T03' on card; got: '📝 E2E-Beta-Tester-221446-T03, E2E-Beta-City:\ndodaj notatkę "zainteresowany pompą ciepła"?' |
| `card_contains_note_content` | ✅ `pass` | expected note text in card; got: '📝 E2E-Beta-Tester-221446-T03, E2E-Beta-City:\ndodaj notatkę "zainteresowany pompą ciepła"?' |
| `three_button_mutation_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `save_button_present` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Notatka dodana.' |
| `sheets_row_created` | ✅ `pass` | row 74 matched |
| `sheets_row_created_field_Notatki` | ✅ `pass` | row['Notatki']='[19.05.2026]: zainteresowany pompą ciepła' contains 'pompą' |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-221446-T03'
note_content: 'zainteresowany pompą ciepła'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-221446-T03, E2E-Beta-City, 600100200, PV'
setup_co_dalej_closed: True
note_trigger: 'dodaj notatkę: zainteresowany pompą ciepła'
reply_count: 1
save_confirmed_co_dalej_closed: False
```
</details>

---
