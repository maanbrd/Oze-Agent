# OZE-Agent E2E Report ✅

_Generated: 2026-05-19T20:47:33.572741+00:00_

**Overall:** PASS
**Scenarios:** 1 (pass 1, blocker 0)

**Check tag counts:** ✅ pass=13, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=0, 🛑 blocker=0

## ✅ Clean PASS

## ✅ `post_drive_photo_smoke` — PASS  _[post_campaign_apps]_

- started: `2026-05-19T20:46:35.200186+00:00`
- ended:   `2026-05-19T20:47:33.572555+00:00` (58.4s)

| Check | Tag | Detail |
|---|---|---|
| `client_absent_before_trigger` | ✅ `pass` | None |
| `no_sheet_write_before_client_confirm` | ✅ `pass` | None |
| `client_save_button` | ✅ `pass` | ✅ Zapisać |
| `client_save_confirmed` | ✅ `pass` | got 2 reply(ies); first: '✅ Zapisane.' |
| `sheet_row_after_client_confirm` | ✅ `pass` | {'Imię i nazwisko': 'Agnieszka Lewandowska', 'Telefon': '607998877', 'Email': 'agnieszka.lewandowska+204635-58ddac@e2e-noinbox.local', 'Miasto': 'Kalisz', 'Adres': 'ul. Ogrodowa 4', 'Status': 'Nowy lead', 'Produkt': 'PV', 'Notatki': 'moc: 8kW', 'Data pierwszego kontaktu': '2026-05-19', 'Data ostatniego kontaktu': '2026-05-19', 'Następny krok': '', 'Data następnego kroku': '', 'Źródło pozyskania': 'Polecenie', 'Zdjęcia': '', 'Link do zdjęć': '', 'ID wydarzenia Kalendarz': '', '_row': 71} |
| `no_drive_sheet_write_before_photo_confirm` | ✅ `pass` |  |
| `photo_save_button` | ✅ `pass` | ✅ Zapisać |
| `sheet_photo_metadata_row_present` | ✅ `pass` | {'Imię i nazwisko': 'Agnieszka Lewandowska', 'Telefon': '607998877', 'Email': 'agnieszka.lewandowska+204635-58ddac@e2e-noinbox.local', 'Miasto': 'Kalisz', 'Adres': 'ul. Ogrodowa 4', 'Status': 'Nowy lead', 'Produkt': 'PV', 'Notatki': 'moc: 8kW', 'Data pierwszego kontaktu': '2026-05-19', 'Data ostatniego kontaktu': '2026-05-19', 'Następny krok': '', 'Data następnego kroku': '', 'Źródło pozyskania': 'Polecenie', 'Zdjęcia': '1', 'Link do zdjęć': 'https://drive.google.com/drive/folders/1UcVDcGbdYoO8x2uUak8GB76tyHI-em88', 'ID wydarzenia Kalendarz': '', '_row': 71} |
| `sheet_photo_count_updated` | ✅ `pass` | 1 |
| `sheet_photo_folder_link_updated` | ✅ `pass` | https://drive.google.com/drive/folders/1UcVDcGbdYoO8x2uUak8GB76tyHI-em88 |
| `drive_file_uploaded` | ✅ `pass` | [{'webViewLink': 'https://drive.google.com/file/d/1AJNYBfinbhdpV6DcQASvsMbI5MQ8SG51/view?usp=drivesdk', 'id': '1AJNYBfinbhdpV6DcQASvsMbI5MQ8SG51', 'name': 'Agnieszka_Lewandowska_20260519_204717.jpg', 'createdTime': '2026-05-19T20:47:19.092Z'}] |
| `drive_folder_cleanup` | ✅ `pass` | 1UcVDcGbdYoO8x2uUak8GB76tyHI-em88 |
| `sheets_calendar_cleanup` | ✅ `pass` | {'user_id': 'bd381405-66d2-4544-b817-117f8f8de441', 'run_id': None, 'include_fixtures': False, 'cleanup_safe': True, 'sheets_rows_found': 1, 'sheets_deleted': 1, 'linked_calendar_events_found': 0, 'linked_calendar_deleted': 0, 'calendar_events_found': 0, 'calendar_deleted': 0} |

<details><summary>Context</summary>

```
user_id: 'bd381405-66d2-4544-b817-117f8f8de441'
client_name: 'Agnieszka Lewandowska'
client_city: 'Kalisz'
client_email: 'agnieszka.lewandowska+204635-58ddac@e2e-noinbox.local'
add_client_trigger: 'dodaj klienta Agnieszka Lewandowska, Kalisz, ul. Ogrodowa 4, telefon 607998877, email agnieszka.lewandowska+204635-58ddac@e2e-noinbox.local, fotowoltaika 8 kW, polecenie'
add_client_card_replies: ['📋 Agnieszka Lewandowska, ul. Ogrodowa 4, Kalisz\nPV\nTel. 607 998 877\nEmail: agnieszka.lewandowska+204635-58ddac@e2e-noinbox.local\nNotatki: moc: 8kW\nŹródło: Polecenie\nZapisać / dopisać / anulować?']
client_save_confirmed_co_dalej_closed: True
add_client_save_replies: ['✅ Zapisane.', 'Co dalej — Agnieszka Lewandowska (Kalisz)? Spotkanie, telefon, mail, odłożyć na później?']
photo_card_replies: ['📸 Zapisać zdjęcie do folderu: Agnieszka Lewandowska, Kalisz, ul. Ogrodowa 4?\nPo zapisie: Przez 15 minut kolejne zdjęcia bez opisu wrzucę do tego klienta. Żeby zmienić klienta, napisz w opisie zdjęcia: zdjęcia do [imię nazwisko miasto].']
photo_save_replies: ['📤 Przesyłam zdjęcie...', '📸 Dodane do: Agnieszka Lewandowska, Kalisz, ul. Ogrodowa 4. Przez 15 minut kolejne zdjęcia bez opisu wrzucę do tego klienta. Żeby zmienić klienta, napisz w opisie: zdjęcia do [imię nazwisko miasto].']
drive_folder_id: '1UcVDcGbdYoO8x2uUak8GB76tyHI-em88'
drive_photos: [{'webViewLink': 'https://drive.google.com/file/d/1AJNYBfinbhdpV6DcQASvsMbI5MQ8SG51/view?usp=drivesdk', 'id': '1AJNYBfinbhdpV6DcQASvsMbI5MQ8SG51', 'name': 'Agnieszka_Lewandowska_20260519_204717.jpg', 'createdTime': '2026-05-19T20:47:19.092Z'}]
cleanup: {'user_id': 'bd381405-66d2-4544-b817-117f8f8de441', 'run_id': None, 'include_fixtures': False, 'cleanup_safe': True, 'sheets_rows_found': 1, 'sheets_deleted': 1, 'linked_calendar_events_found': 0, 'linked_calendar_deleted': 0, 'calendar_events_found': 0, 'calendar_deleted': 0}
```
</details>

---
