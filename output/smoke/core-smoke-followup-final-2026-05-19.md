# OZE-Agent E2E Report ✅

_Generated: 2026-05-19T20:42:12.592903+00:00_

**Overall:** PASS
**Scenarios:** 5 (pass 5, blocker 0)

**Check tag counts:** ✅ pass=116, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=0, 🛑 blocker=0

## ✅ Clean PASS

## ✅ `sm10_r6_memory_window_expired_requires_client` — PASS  _[core_smoke]_

- started: `2026-05-19T20:37:33.082400+00:00`
- ended:   `2026-05-19T20:38:31.078967+00:00` (58.0s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-223733-SM10' setup OK |
| `setup_sheet_row_created` | ✅ `pass` | row 71 matched |
| `setup_sheet_row_created_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `conversation_history_expired` | ✅ `pass` | created_at shifted 31 minutes back |
| `no_add_note_card_without_recent_context` | ✅ `pass` | [] |
| `asks_for_client_after_memory_expiry` | ✅ `pass` | podaj imię i nazwisko klienta, miasto i treść notatki. ↵ np.: 'dodaj notatkę do jana kowalskiego z warszawy: dzwonił w sprawie gwarancji' |
| `sheet_row_still_present` | ✅ `pass` | row 71 matched |
| `sheet_row_still_present_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `note_not_appended_without_context` | ✅ `pass` |  |

<details><summary>Context</summary>

```
setup_trigger: 'dodaj klienta E2E-Beta-Tester-223733-SM10, Płock, 600100200, fotowoltaika i magazyn energii'
setup_co_dalej_closed: True
trigger: 'dodaj notatkę: zainteresowany pompą'
note_without_context_replies: ["Podaj imię i nazwisko klienta, miasto i treść notatki.\nNp.: 'dodaj notatkę do Jana Kowalskiego z Warszawy: dzwonił w sprawie gwarancji'"]
```
</details>

## ✅ `sm1_compound_meeting_new_client_preseed` — PASS  _[core_smoke]_

- started: `2026-05-19T20:38:35.581437+00:00`
- ended:   `2026-05-19T20:39:27.594442+00:00` (52.0s)

| Check | Tag | Detail |
|---|---|---|
| `meeting_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_product` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-223835-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-223835-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-223835-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-223835-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-223835-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-223835-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='2i799glr4nim6kcraut65120mo' title='Spotkanie — E2E-Beta-Tester-223835-SM1' |
| `calendar_event_after_meeting_confirm_event_type` | ✅ `pass` | event_type='in_person' matches |
| `calendar_event_after_meeting_confirm_start_time` | ✅ `pass` | event start='2026-05-20T14:00:00+02:00' matches expected '2026-05-20T14:00:00+02:00' (diff 0.0 min) |
| `calendar_event_after_meeting_confirm_duration_min` | ✅ `pass` | duration=60min matches |
| `no_sheet_row_before_seeded_client_confirm` | ✅ `pass` | None |
| `seeded_client_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_client_save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Zapisane.' |
| `seeded_client_sheet_row_created` | ✅ `pass` | row 72 matched |
| `seeded_client_sheet_row_created_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `seeded_client_sheet_row_created_field_Adres` | ✅ `pass` | row['Adres']='Zielona 28' contains 'Zielona' |
| `seeded_client_sheet_row_created_field_Produkt` | ✅ `pass` | row['Produkt']='PV + Magazyn energii' contains 'PV' |
| `seeded_client_sheet_row_created_field_Następny krok` | ✅ `pass` | row['Następny krok']='Spotkanie' contains 'Spotkanie' |

<details><summary>Context</summary>

```
trigger: 'Dodaj spotkanie z E2E-Beta-Tester-223835-SM1 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600100200. Interesuje go fotowoltaika i magazyn energii.'
context_isolated_before_trigger: True
initial_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-223835-SM1\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: Marki, ul. Zielona 28\n• Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E-Beta-Tester-223835-SM1, Zielona 28, Marki\nPV + Magazyn energii\nTel. 600 100 200\nNastępny krok: Spotkanie\nStatus: Spotkanie umówione\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['✅ Zapisane.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

## ✅ `sm2_voice_compound_meeting_new_client_preseed` — PASS  _[core_smoke]_

- started: `2026-05-19T20:39:32.096757+00:00`
- ended:   `2026-05-19T20:40:37.487757+00:00` (65.4s)

| Check | Tag | Detail |
|---|---|---|
| `voice_file_generated` | ✅ `pass` | /tmp/oze-core-smoke-223932.ogg |
| `voice_transcript_card` | ✅ `pass` | ['✅ Zapisz', '❌ Anuluj'] |
| `voice_card_has_two_buttons` | ✅ `pass` | ['✅ Zapisz', '❌ Anuluj'] |
| `voice_card_mentions_transcript` | ✅ `pass` | 🎙 Transkrypcja (pewność: 37%): ↵  ↵ Dodaj spotkanie z E2E Beta Tester 223932 SM2 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600 10 02 00. Interesuje go fotowoltaika i magazyn energii. ↵  ↵ Co z tym? |
| `voice_save_button` | ✅ `pass` | ✅ Zapisz |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magaz |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magaz |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: Spotka |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: Spotka |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: Spotka |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: Spotka |
| `card_contains_product` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 223932 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ulica Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: Spotka |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 223932 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 223932 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 223932 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 223932 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 223932 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='eb3gae4h9878e7dkta79vgh1o8' title='Spotkanie — E2E Beta Tester 223932 SM2' |
| `calendar_event_after_meeting_confirm_event_type` | ✅ `pass` | event_type='in_person' matches |
| `calendar_event_after_meeting_confirm_start_time` | ✅ `pass` | event start='2026-05-20T14:00:00+02:00' matches expected '2026-05-20T14:00:00+02:00' (diff 0.0 min) |
| `calendar_event_after_meeting_confirm_duration_min` | ✅ `pass` | duration=60min matches |
| `no_sheet_row_before_seeded_client_confirm` | ✅ `pass` | None |
| `seeded_client_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_client_save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Zapisane.' |
| `seeded_client_sheet_row_created` | ✅ `pass` | row 73 matched |
| `seeded_client_sheet_row_created_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `seeded_client_sheet_row_created_field_Adres` | ✅ `pass` | row['Adres']='Zielona 28' contains 'Zielona' |
| `seeded_client_sheet_row_created_field_Produkt` | ✅ `pass` | row['Produkt']='PV + Magazyn energii' contains 'PV' |
| `seeded_client_sheet_row_created_field_Następny krok` | ✅ `pass` | row['Następny krok']='Spotkanie' contains 'Spotkanie' |

<details><summary>Context</summary>

```
context_isolated_before_trigger: True
voice_replies: ['🎙 Transkrybuję...', '🎙 Transkrypcja (pewność: 37%):\n\nDodaj spotkanie z E2E Beta Tester 223932 SM2 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600 10 02 00. Interesuje go fotowoltaika i magazyn energii.\n\nCo z tym?']
post_voice_confirm_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E Beta Tester 223932 SM2\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: Marki, ulica Zielona 28\n• Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii\n\n⚠️ Uwaga: masz już spotkanie o tej porze: Spotka']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E Beta Tester 223932 SM2, Zielona 28, Marki\nPV + Magazyn energii\nTel. 600 100 200\nNastępny krok: Spotkanie\nStatus: Spotkanie umówione\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['✅ Zapisane.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

## ✅ `sm3_phone_field_does_not_force_meeting` — PASS  _[core_smoke]_

- started: `2026-05-19T20:40:41.990360+00:00`
- ended:   `2026-05-19T20:41:14.642188+00:00` (32.7s)

| Check | Tag | Detail |
|---|---|---|
| `add_client_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `card_is_add_client_not_meeting` | ✅ `pass` | 📋 E2E-Beta-Tester-224041-SM3 ↵ Tel. 600 100 200 ↵ Notatki: jutro podeślę dane ↵ ❓ Brakuje: Email, Adres, Produkt, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `card_contains_phone` | ✅ `pass` | 📋 E2E-Beta-Tester-224041-SM3 ↵ Tel. 600 100 200 ↵ Notatki: jutro podeślę dane ↵ ❓ Brakuje: Email, Adres, Produkt, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `no_sheet_write_before_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_confirm` | ✅ `pass` |  |
| `save_button` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ✅ `pass` | got 2 reply(ies); first: '✅ Zapisane.' |
| `client_sheet_row_created` | ✅ `pass` | row 74 matched |
| `client_sheet_row_created_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `no_calendar_event_after_add_client_save` | ✅ `pass` |  |

<details><summary>Context</summary>

```
trigger: 'Dodaj klienta E2E-Beta-Tester-224041-SM3, telefon 600100200, jutro podeślę dane'
context_isolated_before_trigger: True
initial_replies: ['📋 E2E-Beta-Tester-224041-SM3\nTel. 600 100 200\nNotatki: jutro podeślę dane\n❓ Brakuje: Email, Adres, Produkt, Źródło pozyskania\nZapisać / dopisać / anulować?']
save_label: '✅ Zapisać'
confirm_replies: ['✅ Zapisane.', 'Co dalej — E2E-Beta-Tester-224041-SM3? Spotkanie, telefon, mail, odłożyć na później?']
save_confirmed_co_dalej_closed: True
```
</details>

## ✅ `sm7_add_meeting_new_client_preseed` — PASS  _[core_smoke]_

- started: `2026-05-19T20:41:19.144579+00:00`
- ended:   `2026-05-19T20:42:12.590049+00:00` (53.4s)

| Check | Tag | Detail |
|---|---|---|
| `meeting_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Ma |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Ma |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_product` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-224119-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Otwock, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-224119-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-224119-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-224119-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-224119-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-224119-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='k6t9dmqlqi953udn92fofrc9pc' title='Spotkanie — E2E-Beta-Tester-224119-SM7' |
| `calendar_event_after_meeting_confirm_event_type` | ✅ `pass` | event_type='in_person' matches |
| `calendar_event_after_meeting_confirm_start_time` | ✅ `pass` | event start='2026-05-20T15:20:00+02:00' matches expected '2026-05-20T15:20:00+02:00' (diff 0.0 min) |
| `calendar_event_after_meeting_confirm_duration_min` | ✅ `pass` | duration=60min matches |
| `no_sheet_row_before_seeded_client_confirm` | ✅ `pass` | None |
| `seeded_client_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_client_save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Zapisane.' |
| `seeded_client_sheet_row_created` | ✅ `pass` | row 75 matched |
| `seeded_client_sheet_row_created_field_Telefon` | ✅ `pass` | row['Telefon']='600100200' contains '600100200' |
| `seeded_client_sheet_row_created_field_Adres` | ✅ `pass` | row['Adres']='ul. Zielona 28' contains 'Zielona' |
| `seeded_client_sheet_row_created_field_Produkt` | ✅ `pass` | row['Produkt']='PV + Magazyn energii' contains 'PV' |
| `seeded_client_sheet_row_created_field_Następny krok` | ✅ `pass` | row['Następny krok']='Spotkanie' contains 'Spotkanie' |

<details><summary>Context</summary>

```
trigger: 'Jutro o 15:20 spotkanie z E2E-Beta-Tester-224119-SM7. Otwock, ul. Zielona 28, telefon 600100200, fotowoltaika i magazyn energii.'
context_isolated_before_trigger: True
initial_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-224119-SM7\n• Data: 20.05.2026 (środa)\n• Godzina: 15:20\n• Czas trwania: 60 min\n• Miejsce: Otwock, ul. Zielona 28\n• Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E-Beta-Tester-224119-SM7, ul. Zielona 28, Otwock\nPV + Magazyn energii\nTel. 600 100 200\nNastępny krok: Spotkanie\nStatus: Spotkanie umówione\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['✅ Zapisane.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

---
