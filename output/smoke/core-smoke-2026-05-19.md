# OZE-Agent E2E Report 🛑

_Generated: 2026-05-19T18:39:49.169282+00:00_

**Overall:** BLOCKER
**Scenarios:** 5 (pass 0, blocker 1)

**Check tag counts:** ✅ pass=69, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=19, 🛑 blocker=1

## 🛑 Blockers

## 🛑 `sm10_r6_memory_window_expired_requires_client` — BLOCKER  _[core_smoke]_

- started: `2026-05-19T18:35:39.638575+00:00`
- ended:   `2026-05-19T18:36:04.258278+00:00` (24.6s)

| Check | Tag | Detail |
|---|---|---|
| `setup_save_confirmed` | 🛑 `blocker` | setup save reply lacks confirm marker; got ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spr'] |

<details><summary>Context</summary>

```
setup_trigger: 'dodaj klienta E2E-Beta-Tester-203539-SM10, Płock, 600100200, fotowoltaika i magazyn energii'
```
</details>

---

## ❌ Fails

## ❌ `sm1_compound_meeting_new_client_preseed` — FAIL  _[core_smoke]_

- started: `2026-05-19T18:36:08.762145+00:00`
- ended:   `2026-05-19T18:37:06.673765+00:00` (57.9s)

| Check | Tag | Detail |
|---|---|---|
| `meeting_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203608-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn ene |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203608-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn ene |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203608-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203608-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203608-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203608-SM1 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203608-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203608-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203608-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203608-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203608-SM1, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Następny krok: Spotkanie ↵ Status: Spotkanie umówione ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='h6aqeigsvbrt2sakahval4kmpk' title='Spotkanie — E2E-Beta-Tester-203608-SM1' |
| `calendar_event_after_meeting_confirm_event_type` | ✅ `pass` | event_type='in_person' matches |
| `calendar_event_after_meeting_confirm_start_time` | ✅ `pass` | event start='2026-05-20T14:00:00+02:00' matches expected '2026-05-20T14:00:00+02:00' (diff 0.0 min) |
| `calendar_event_after_meeting_confirm_duration_min` | ✅ `pass` | duration=60min matches |
| `no_sheet_row_before_seeded_client_confirm` | ✅ `pass` | None |
| `seeded_client_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_client_save_confirmed` | ❌ `fail` | got 1 reply(ies); first: '⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.' |
| `seeded_client_sheet_row_created` | ❌ `fail` | no Sheets row matched name='E2E-Beta-Tester-203608-SM1' city='Marki' |

<details><summary>Context</summary>

```
trigger: 'Dodaj spotkanie z E2E-Beta-Tester-203608-SM1 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600100200. Interesuje go fotowoltaika i magazyn energii.'
initial_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-203608-SM1\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: Zielona 28, Marki\n• Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E-Beta-Tester-203608-SM1, Zielona 28, Marki\nPV + Magazyn energii\nTel. 600 100 200\nNastępny krok: Spotkanie\nStatus: Spotkanie umówione\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
seeded_client_save_confirmed_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

## ❌ `sm2_voice_compound_meeting_new_client_preseed` — FAIL  _[core_smoke]_

- started: `2026-05-19T18:37:11.180906+00:00`
- ended:   `2026-05-19T18:38:16.027422+00:00` (64.8s)

| Check | Tag | Detail |
|---|---|---|
| `voice_file_generated` | ✅ `pass` | /tmp/oze-core-smoke-203711.ogg |
| `voice_transcript_card` | ✅ `pass` | ['✅ Zapisz', '❌ Anuluj'] |
| `voice_card_has_two_buttons` | ✅ `pass` | ['✅ Zapisz', '❌ Anuluj'] |
| `voice_card_mentions_transcript` | ✅ `pass` | 🎙 Transkrypcja (pewność: 39%): ↵  ↵ Dodaj spotkanie z E2E Beta Tester 203 711 SM2 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600 10 02 00. Interesuje go fotowoltaika i magazyn energii. ↵  ↵ Co z tym? |
| `voice_save_button` | ✅ `pass` | ✅ Zapisz |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 203711 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn ene |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 203711 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn ene |
| `card_contains_client_name` | ❌ `fail` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 203711 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 203711 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 203711 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E Beta Tester 203711 SM2 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 14:00 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Marki ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii ↵  ↵ ⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 203711 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 203711 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 203711 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_phone` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 203711 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `seeded_card_contains_product` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E Beta Tester 203711 SM2, Zielona 28, Marki ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `calendar_event_after_meeting_confirm` | ❌ `fail` | no Calendar event matched summary~='E2E-Beta-Tester-203711-SM2' in [2026-05-20T13:50:00+02:00, 2026-05-20T15:10:00+02:00) |
| `no_sheet_row_before_seeded_client_confirm` | ✅ `pass` | None |
| `seeded_client_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_client_save_confirmed` | ❌ `fail` | got 1 reply(ies); first: '⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.' |
| `seeded_client_sheet_row_created` | ❌ `fail` | no Sheets row matched name='E2E-Beta-Tester-203711-SM2' city='Marki' |

<details><summary>Context</summary>

```
voice_replies: ['🎙 Transkrybuję...', '🎙 Transkrypcja (pewność: 39%):\n\nDodaj spotkanie z E2E Beta Tester 203 711 SM2 na jutro o 14. Mieszka w Marki na ulicy Zielonej 28. Telefon 600 10 02 00. Interesuje go fotowoltaika i magazyn energii.\n\nCo z tym?']
post_voice_confirm_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E Beta Tester 203711 SM2\n• Data: 20.05.2026 (środa)\n• Godzina: 14:00\n• Czas trwania: 60 min\n• Miejsce: Zielona 28, Marki\n• Dane klienta do zapisu: Tel.: 600100200; Adres: Zielona 28; Produkt: PV + Magazyn energii\n\n⚠️ Uwaga: masz już spotkanie o tej porze: E2E-Beta-Fix']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E Beta Tester 203711 SM2, Zielona 28, Marki\nPV + Magazyn energii\nTel. 600 100 200\nStatus: Spotkanie umówione\nNastępny krok: Spotkanie\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / dopisać / anulować?']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
seeded_client_save_confirmed_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

## ❌ `sm3_phone_field_does_not_force_meeting` — FAIL  _[core_smoke]_

- started: `2026-05-19T18:38:20.530236+00:00`
- ended:   `2026-05-19T18:38:51.364641+00:00` (30.8s)

| Check | Tag | Detail |
|---|---|---|
| `add_client_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `card_is_add_client_not_meeting` | ❌ `fail` | 📋 E2E-Beta-Tester-203820-SM3 ↵ Tel. 600 100 200 ↵ Notatki: Jutro zostaną przesłane dane ↵ ❓ Brakuje: Email, Adres, Produkt, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `card_contains_phone` | ❌ `fail` | 📋 E2E-Beta-Tester-203820-SM3 ↵ Tel. 600 100 200 ↵ Notatki: Jutro zostaną przesłane dane ↵ ❓ Brakuje: Email, Adres, Produkt, Źródło pozyskania ↵ Zapisać / dopisać / anulować? |
| `no_sheet_write_before_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_confirm` | ✅ `pass` |  |
| `save_button` | ✅ `pass` | ✅ Zapisać |
| `save_confirmed` | ❌ `fail` | got 1 reply(ies); first: '⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.' |
| `client_sheet_row_created` | ❌ `fail` | no Sheets row matched name='E2E-Beta-Tester-203820-SM3' city=None |
| `no_calendar_event_after_add_client_save` | ✅ `pass` |  |

<details><summary>Context</summary>

```
trigger: 'Dodaj klienta E2E-Beta-Tester-203820-SM3, telefon 600100200, jutro podeślę dane'
initial_replies: ['📋 E2E-Beta-Tester-203820-SM3\nTel. 600 100 200\nNotatki: Jutro zostaną przesłane dane\n❓ Brakuje: Email, Adres, Produkt, Źródło pozyskania\nZapisać / dopisać / anulować?']
save_label: '✅ Zapisać'
confirm_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
save_confirmed_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
save_confirmed_co_dalej_closed: False
```
</details>

## ❌ `sm7_add_meeting_new_client_preseed` — FAIL  _[core_smoke]_

- started: `2026-05-19T18:38:55.867200+00:00`
- ended:   `2026-05-19T18:39:49.166229+00:00` (53.3s)

| Check | Tag | Detail |
|---|---|---|
| `meeting_card_arrived` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `meeting_three_button_card` | ✅ `pass` | 3-button card found, labels=['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `first_card_is_meeting_not_client` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203855-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Otwock ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazy |
| `first_card_not_add_client_heading` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203855-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Otwock ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazy |
| `card_contains_client_name` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203855-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Otwock ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_city` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203855-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Otwock ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_address` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203855-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Otwock ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `card_contains_phone` | ✅ `pass` | ✅ Dodać spotkanie? ↵  ↵ • Klient: E2E-Beta-Tester-203855-SM7 ↵ • Data: 20.05.2026 (środa) ↵ • Godzina: 15:20 ↵ • Czas trwania: 60 min ↵ • Miejsce: Zielona 28, Otwock ↵ • Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii |
| `meeting_card_no_internal_leak` | ✅ `pass` | no internal fields leaked |
| `no_sheet_write_before_meeting_confirm` | ✅ `pass` | None |
| `no_calendar_write_before_meeting_confirm` | ✅ `pass` |  |
| `meeting_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_add_client_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `seeded_card_contains_client_name` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203855-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Data nastepnego kroku: 2026-05-20 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / d |
| `seeded_card_contains_city` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203855-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Data nastepnego kroku: 2026-05-20 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / d |
| `seeded_card_contains_address` | ✅ `pass` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203855-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Data nastepnego kroku: 2026-05-20 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / d |
| `seeded_card_contains_phone` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203855-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Data nastepnego kroku: 2026-05-20 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / d |
| `seeded_card_contains_product` | ❌ `fail` | ✅ Spotkanie dodane do kalendarza. ↵ 📋 E2E-Beta-Tester-203855-SM7, ul. Zielona 28, Otwock ↵ PV + Magazyn energii ↵ Tel. 600 100 200 ↵ Data nastepnego kroku: 2026-05-20 ↵ Status: Spotkanie umówione ↵ Następny krok: Spotkanie ↵ Data następnego kroku: 20.05.2026 (środa) ↵ ❓ Brakuje: Email, Źródło pozyskania ↵ Zapisać / d |
| `calendar_event_after_meeting_confirm` | ✅ `pass` | event id='nhu74u2qttqb8eof6v832uj0dg' title='Spotkanie — E2E-Beta-Tester-203855-SM7' |
| `calendar_event_after_meeting_confirm_event_type` | ✅ `pass` | event_type='in_person' matches |
| `calendar_event_after_meeting_confirm_start_time` | ✅ `pass` | event start='2026-05-20T15:20:00+02:00' matches expected '2026-05-20T15:20:00+02:00' (diff 0.0 min) |
| `calendar_event_after_meeting_confirm_duration_min` | ✅ `pass` | duration=60min matches |
| `no_sheet_row_before_seeded_client_confirm` | ✅ `pass` | None |
| `seeded_client_save_button` | ✅ `pass` | ✅ Zapisać |
| `seeded_client_save_confirmed` | ❌ `fail` | got 1 reply(ies); first: '⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.' |
| `seeded_client_sheet_row_created` | ❌ `fail` | no Sheets row matched name='E2E-Beta-Tester-203855-SM7' city='Otwock' |

<details><summary>Context</summary>

```
trigger: 'Jutro o 15:20 spotkanie z E2E-Beta-Tester-203855-SM7. Otwock, ul. Zielona 28, telefon 600100200, fotowoltaika i magazyn energii.'
initial_replies: ['✅ Dodać spotkanie?\n\n• Klient: E2E-Beta-Tester-203855-SM7\n• Data: 20.05.2026 (środa)\n• Godzina: 15:20\n• Czas trwania: 60 min\n• Miejsce: Zielona 28, Otwock\n• Dane klienta do zapisu: Tel.: 600100200; Adres: ul. Zielona 28; Produkt: PV + Magazyn energii']
meeting_save_label: '✅ Zapisać'
meeting_save_replies: ['✅ Spotkanie dodane do kalendarza.\n📋 E2E-Beta-Tester-203855-SM7, ul. Zielona 28, Otwock\nPV + Magazyn energii\nTel. 600 100 200\nData nastepnego kroku: 2026-05-20\nStatus: Spotkanie umówione\nNastępny krok: Spotkanie\nData następnego kroku: 20.05.2026 (środa)\n❓ Brakuje: Email, Źródło pozyskania\nZapisać / d']
seeded_client_save_label: '✅ Zapisać'
seeded_client_save_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
seeded_client_save_confirmed_replies: ['⚠️ Google Sheets jest chwilowo niedostępny. Twoje dane NIE zostały zapisane. Spróbuj ponownie za kilka minut.']
seeded_client_save_confirmed_co_dalej_closed: False
```
</details>

---
