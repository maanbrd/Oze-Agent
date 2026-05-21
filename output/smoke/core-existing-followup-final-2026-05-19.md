# OZE-Agent E2E Report ✅

_Generated: 2026-05-19T20:36:41.661378+00:00_

**Overall:** PASS
**Scenarios:** 5 (pass 5, blocker 0)

**Check tag counts:** ✅ pass=45, ⚠️ known_drift=1, 🟡 expected_fail=0, ❌ fail=0, 🛑 blocker=0

## ⚠️ Known drifts (PASS but log)

## ✅ `add_meeting_phone_call_save` — PASS  _[mutating_core]_

- started: `2026-05-19T20:30:29.692066+00:00`
- ended:   `2026-05-19T20:31:44.418162+00:00` (74.7s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-223029-B07' setup OK |
| `got_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `three_button_mutation_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |
| `no_internal_field_leak` | ✅ `pass` | no internal fields leaked |
| `card_has_phone_icon` | ⚠️ `known_drift` | icon=None, header='✅ Dodać telefon?' — _ref: INTENCJE_MVP.md §4 — phone-call card uses 📞 icon_ |
| `card_mentions_meeting_date` | ✅ `pass` | expected '21.05.2026' (PL) or its ISO form in card; got: '✅ Dodać telefon?\n\n• Klient: E2E-Beta-Tester-223029-B07\n• Data: 21.05.2026 (czwartek)\n• Godzina: 10:00\n• Czas trwania: 15 min\n• Miejsce: telefonicznie' |
| `pl_date_format` | ✅ `pass` | PL date format OK |
| `save_button_present` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Telefon dodany do kalendarza.' |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-223029-B07'
expected_pl_date: '21.05.2026 (Czwartek)'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-223029-B07, E2E-Beta-City, 600100200, PV'
setup_co_dalej_closed: True
trigger: 'zadzwonię 21.05.2026 o 10:00 do E2E-Beta-Tester-223029-B07, E2E-Beta-City'
reply_count: 1
save_label: '✅ Zapisać'
confirm_replies: ['✅ Telefon dodany do kalendarza.']
save_confirmed_co_dalej_closed: False
```
</details>

---

## ✅ Clean PASS

## ✅ `add_client_dup_dopisac_update_path` — PASS  _[mutating_core]_

- started: `2026-05-19T20:31:48.919822+00:00`
- ended:   `2026-05-19T20:33:40.193846+00:00` (111.3s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'Oskar Stabilski' setup OK |
| `setup_sheets_row_ready` | ✅ `pass` | row 72 matched |
| `setup_sheets_row_ready_field_Telefon` | ✅ `pass` | row['Telefon']='612068167' contains '612068167' |
| `setup_sheets_row_ready_field_Email` | ✅ `pass` | row['Email']='e2e.test.223148.b11@e2e-noinbox.local' contains 'e2e.test.223148.b11@e2e-noinbox.local' |
| `got_dup_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `duplicate_update_card_detected` | ✅ `pass` | card text: 'Mam już Oskar Stabilski (Wrocław).\nZaktualizować o: Imię i nazwisko, Telefon, Email, Miasto, Produkt?' |
| `dopisac_button_present` | ✅ `pass` | ➕ Dopisać |
| `bot_asked_what_to_add` | ✅ `pass` | expected 'Co chcesz dopisać?' prompt; got ['Co chcesz dopisać?'] |
| `post_dopisac_update_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `post_dopisac_card_is_duplicate_update` | ✅ `pass` | card text: 'Zaktualizować Oskar Stabilski (Wrocław) o:\nAdres: ul. Stabilna 7?' |
| `final_save_button_present` | ✅ `pass` | ✅ Zapisać |
| `final_save_confirmed` | ✅ `pass` | got 2 reply(ies); first: '✅ Dane zaktualizowane.' |
| `sheets_row_updated_with_new_address` | ✅ `pass` | row 72 matched |
| `sheets_row_updated_with_new_address_field_Adres` | ✅ `pass` | row['Adres']='ul. Stabilna 7' contains 'ul. Stabilna 7' |

<details><summary>Context</summary>

```
client_name: 'Oskar Stabilski'
client_city: 'Wrocław'
setup_email: 'e2e.test.223148.b11@e2e-noinbox.local'
new_address: 'ul. Stabilna 7'
setup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 612068167, e2e.test.223148.b11@e2e-noinbox.local, PV'
setup_co_dalej_closed: True
dup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 612068167, e2e.test.223148.b11@e2e-noinbox.local, PV'
reply_count: 1
post_dopisac_reply_count: 1
dopisac_text: 'adres: ul. Stabilna 7'
update_reply_count: 1
final_save_confirmed_co_dalej_closed: True
```
</details>

## ✅ `show_client_multi_match_disambig` — PASS  _[read_only]_

- started: `2026-05-19T20:33:44.695512+00:00`
- ended:   `2026-05-19T20:33:51.722140+00:00` (7.0s)

| Check | Tag | Detail |
|---|---|---|
| `offers_disambig` | ✅ `pass` | expected disambig prompt or ≥2 button options; got: 'Mam 4 klientów:\n1. Jan Kowalski — Warszawa\n2. Jan Kowalski — Warszawa\n3. Jan Kowalski — Kraków\n4. Jan Kowalski — Warszawa\nKtórego?' |
| `lists_warszawa_match` | ✅ `pass` | expected 'Warszawa' marker; got: 'Mam 4 klientów:\n1. Jan Kowalski — Warszawa\n2. Jan Kowalski — Warszawa\n3. Jan Kowalski — Kraków\n4. Jan Kowalski — Warszawa\nKtórego?' |
| `no_mutation_buttons` | ✅ `pass` | buttons=['1. Jan Kowalski — Warszawa', '2. Jan Kowalski — Warszawa', '3. Jan Kowalski — Kraków', '4. Jan Kowalski — Warszawa'] |
| `no_banned_phrases` | ✅ `pass` | no banned phrases |

<details><summary>Context</summary>

```
trigger: 'pokaż Jana Kowalskiego'
fixture_dependency: 'Run mcp__oze-e2e__e2e_seed_fixtures before this scenario. Two E2E-Beta-Fixture-Jan-Kowalski rows must exist (Warszawa + Kraków).'
reply_count: 1
reply_text: 'Mam 4 klientów:\n1. Jan Kowalski — Warszawa\n2. Jan Kowalski — Warszawa\n3. Jan Kowalski — Kraków\n4. Jan Kowalski — Warszawa\nKtórego?'
reply_buttons: ['1. Jan Kowalski — Warszawa', '2. Jan Kowalski — Warszawa', '3. Jan Kowalski — Kraków', '4. Jan Kowalski — Warszawa']
```
</details>

## ✅ `r7_next_action_prompt_after_add_client` — PASS  _[rules]_

- started: `2026-05-19T20:33:56.224538+00:00`
- ended:   `2026-05-19T20:35:18.334014+00:00` (82.1s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_committed` | ✅ `pass` | client E2E-Beta-Tester-223356-T04 created |
| `bot_emitted_co_dalej_prompt` | ✅ `pass` | R7 needs the 'Co dalej' prompt; replies: ['✅ Zapisane.', 'Co dalej — E2E-Beta-Tester-223356-T04 (E2E-Beta-City)? Spotkanie, telefon, mail, odłożyć na później?'] |
| `got_meeting_card_via_r7` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_card_references_client` | ✅ `pass` | expected 'E2E-Beta-Tester-223356-T04'; got: '✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-223356-T04\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: E2E-Beta-City\n• Status: Nowy lead → Spotkanie umówione\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Bet' |
| `meeting_card_has_14_00` | ✅ `pass` | expected '14:00'; got: '✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-223356-T04\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: E2E-Beta-City\n• Status: Nowy lead → Spotkanie umówione\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Bet' |
| `meeting_save_button_present` | ✅ `pass` | ✅ Zapisać |
| `meeting_saved` | ✅ `pass` | got 1 reply(ies); first: '✅ Spotkanie dodane do kalendarza. Status klienta: Spotkanie umówione.' |
| `calendar_event_created` | ✅ `pass` | event id='4kcau2utahm2e503ku5afehers' title='Spotkanie — E2E-Beta-Tester-223356-T04' |
| `calendar_event_created_start_time` | ✅ `pass` | event start='2026-05-20T14:00:00+02:00' matches expected '2026-05-20T14:00:00+02:00' (diff 0.0 min) |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-223356-T04'
add_trigger: 'dodaj klienta E2E-Beta-Tester-223356-T04, E2E-Beta-City, 600100200, PV'
next_action_trigger: 'spotkanie jutro o 14:00'
meeting_reply_count: 1
meeting_saved_co_dalej_closed: False
```
</details>

## ✅ `r6_active_client_implicit_reference` — PASS  _[rules]_

- started: `2026-05-19T20:35:22.836499+00:00`
- ended:   `2026-05-19T20:36:41.658567+00:00` (78.8s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-223522-T03' setup OK |
| `got_note_card_via_active_client` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `card_references_active_client_name` | ✅ `pass` | R6 should put active client 'E2E-Beta-Tester-223522-T03' on card; got: '📝 E2E-Beta-Tester-223522-T03, E2E-Beta-City:\ndodaj notatkę "zainteresowany pompą ciepła"?' |
| `card_contains_note_content` | ✅ `pass` | expected note text in card; got: '📝 E2E-Beta-Tester-223522-T03, E2E-Beta-City:\ndodaj notatkę "zainteresowany pompą ciepła"?' |
| `three_button_mutation_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `save_button_present` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Notatka dodana.' |
| `sheets_row_created` | ✅ `pass` | row 74 matched |
| `sheets_row_created_field_Notatki` | ✅ `pass` | row['Notatki']='[19.05.2026]: zainteresowany pompą ciepła' contains 'pompą' |

<details><summary>Context</summary>

```
client_name: 'E2E-Beta-Tester-223522-T03'
note_content: 'zainteresowany pompą ciepła'
setup_trigger: 'dodaj klienta E2E-Beta-Tester-223522-T03, E2E-Beta-City, 600100200, PV'
setup_co_dalej_closed: True
note_trigger: 'dodaj notatkę: zainteresowany pompą ciepła'
reply_count: 1
save_confirmed_co_dalej_closed: False
```
</details>

---
