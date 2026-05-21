# OZE-Agent E2E Report 🛑

_Generated: 2026-05-19T18:47:56.785791+00:00_

**Overall:** BLOCKER
**Scenarios:** 5 (pass 3, blocker 1)

**Check tag counts:** ✅ pass=93, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=4, 🛑 blocker=1

## 🛑 Blockers

## 🛑 `sm7_add_meeting_new_client_preseed` — BLOCKER  _[core_smoke]_

- started: `2026-05-19T18:47:35.334763+00:00`
- ended:   `2026-05-19T18:47:56.780796+00:00` (21.4s)

| Check | Tag | Detail |
|---|---|---|
| `meeting_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ❌ `fail` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `first_card_not_add_client_heading` | ✅ `pass` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `card_contains_client_name` | ❌ `fail` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `card_contains_city` | ❌ `fail` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `card_contains_address` | ✅ `pass` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `card_contains_phone` | ✅ `pass` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `card_contains_product` | ✅ `pass` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Produkt: PV + Magazyn energii ↵ Adres: ul. Zielona 28 ↵ Zapisać? |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | 🛑 `blocker` | no add_client card after meeting save |

<details><summary>Context</summary>

```
trigger: 'Jutro o 15:20 spotkanie z E2E-Beta-Tester-204735-SM7. Otwock, ul. Zielona 28, telefon 600100200, fotowoltaika i magazyn energii.'
initial_replies: ['Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o:\nTelefon: 600100200\nProdukt: PV + Magazyn energii\nAdres: ul. Zielona 28\nZapisać?']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Zapisane.']
```
</details>

---

## ❌ Fails

## ❌ `sm3_phone_field_does_not_force_meeting` — FAIL  _[core_smoke]_

- started: `2026-05-19T18:47:08.699867+00:00`
- ended:   `2026-05-19T18:47:30.832091+00:00` (22.1s)

| Check | Tag | Detail |
|---|---|---|
| `add_client_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `card_is_add_client_not_meeting` | ✅ `pass` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Zapisać? |
| `card_contains_phone` | ✅ `pass` | Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o: ↵ Telefon: 600100200 ↵ Zapisać? |
| `no_sheet_write_before_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_confirm` | ✅ `pass` |  |
| `save_button` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ✅ `pass` | got 1 reply(ies); first: '✅ Zapisane.' |
| `client_sheet_row_created` | ❌ `fail` | no Sheets row matched name='E2E-Beta-Tester-204708-SM3' city=None |
| `no_calendar_event_after_add_client_save` | ✅ `pass` |  |

<details><summary>Context</summary>

```
trigger: 'Dodaj klienta E2E-Beta-Tester-204708-SM3, telefon 600100200, jutro podeślę dane'
initial_replies: ['Zaktualizować E2E Beta Tester 204601 SM2 (Marki) o:\nTelefon: 600100200\nZapisać?']
save_label: '✅ Zapisać'
confirm_replies: ['✅ Zapisane.']
save_confirmed_co_dalej_closed: False
```
</details>

---

## ✅ Clean PASS

## ✅ `sm10_r6_memory_window_expired_requires_client` — PASS  _[core_smoke]_

- started: `2026-05-19T18:44:09.602779+00:00`
- ended:   `2026-05-19T18:45:01.102457+00:00` (51.5s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'E2E-Beta-Tester-204409-SM10' setup OK |
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
setup_trigger: 'dodaj klienta E2E-Beta-Tester-204409-SM10, Płock, 600100200, fotowoltaika i magazyn energii'
setup_co_dalej_closed: True
trigger: 'dodaj notatkę: zainteresowany pompą'
note_without_context_replies: ["Podaj imię i nazwisko klienta, miasto i treść notatki.\nNp.: 'dodaj notatkę do Jana Kowalskiego z Warszawy: dzwonił w sprawie gwarancji'"]
```
</details>

## ✅ `sm1_compound_meeting_new_client_preseed` — PASS  _[core_smoke]_

- started: `2026-05-19T18:45:05.604881+00:00`
- ended:   `2026-05-19T18:45:57.069648+00:00` (51.5s)

| Check | Tag | Detail |
|---|---|---|
| `meeting_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_product` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-204505-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-204505-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-204505-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-204505-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-204505-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-204505-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='o78fsrg35570g4kh9rav32qr2o' title='Spotkanie — E2E-Beta-Tester-204505-SM1' |
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
trigger: 'Dodaj spotkanie z E2E-Beta-Tester-204505-SM1 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600100200. Interesuje go fotowoltaika i magazyn energii.'
initial_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-204505-SM1\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: Marki, ul. Zielona 28\n• Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E-Beta-Tester-204505-SM1, Zielona 28, Marki\nPV + Magazyn energii\nTel. 600 100 200\nStatus: Spotkanie umówione\nNastępny krok: Spotkanie\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['✅ Zapisane.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

## ✅ `sm2_voice_compound_meeting_new_client_preseed` — PASS  _[core_smoke]_

- started: `2026-05-19T18:46:01.572455+00:00`
- ended:   `2026-05-19T18:47:04.197140+00:00` (62.6s)

| Check | Tag | Detail |
|---|---|---|
| `voice_file_generated` | ✅ `pass` | /tmp/oze-core-smoke-204601.ogg |
| `voice_transcript_card` | ✅ `pass` | ['✅ Zapisz', '❌ Anuluj'] |
| `voice_card_has_two_buttons` | ✅ `pass` | ['✅ Zapisz', '❌ Anuluj'] |
| `voice_card_mentions_transcript` | ✅ `pass` | 🎙 Transkrypcja (pewność: 41%): ↵  ↵ Dodaj spotkanie z E2E Beta Tester 204601 SM2 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600 10 02 00. Interesuje go fotowoltaika i magazyn energii. ↵  ↵ Co z tym? |
| `voice_save_button` | ✅ `pass` | ✅ Zapisz |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `card_contains_product` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 204601 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Marki, ul. Zielona 28 ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 204601 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 204601 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 204601 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 204601 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 204601 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='s6q42mqi944qnfg2fga2m1iij0' title='Spotkanie — E2E Beta Tester 204601 SM2' |
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
voice_replies: ['🎙 Transkrybuję...', '🎙 Transkrypcja (pewność: 41%):\n\nDodaj spotkanie z E2E Beta Tester 204601 SM2 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600 10 02 00. Interesuje go fotowoltaika i magazyn energii.\n\nCo z tym?']
post_voice_confirm_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E Beta Tester 204601 SM2\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: Marki, ul. Zielona 28\n• Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E Beta Tester 204601 SM2, Zielona 28, Marki\nPV + Magazyn energii\nTel. 600 100 200\nNastępny krok: Spotkanie\nStatus: Spotkanie umówione\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['✅ Zapisane.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

---
