# OZE-Agent E2E Report ❌

_Generated: 2026-05-19T20:25:53.699580+00:00_

**Overall:** FAIL
**Scenarios:** 1 (pass 0, blocker 0)

**Check tag counts:** ✅ pass=13, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=1, 🛑 blocker=0

## ❌ Fails

## ❌ `add_client_dup_dopisac_update_path` — FAIL  _[mutating_core]_

- started: `2026-05-19T20:24:05.069742+00:00`
- ended:   `2026-05-19T20:25:53.697390+00:00` (108.6s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'Oskar Stabilski' setup OK |
| `setup_sheets_row_ready` | ✅ `pass` | row 71 matched |
| `setup_sheets_row_ready_field_Telefon` | ✅ `pass` | row['Telefon']='676408040' contains '676408040' |
| `setup_sheets_row_ready_field_Email` | ✅ `pass` | row['Email']='e2e.test.222405.b11@e2e-noinbox.local' contains 'e2e.test.222405.b11@e2e-noinbox.local' |
| `got_dup_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `duplicate_update_card_detected` | ✅ `pass` | card text: 'Mam już Oskar Stabilski (Wrocław).\nZaktualizować o: Imię i nazwisko, Telefon, Email, Miasto, Produkt?' |
| `dopisac_button_present` | ✅ `pass` | ➕ Dopisać |
| `bot_asked_what_to_add` | ✅ `pass` | expected 'Co chcesz dopisać?' prompt; got ['Co chcesz dopisać?'] |
| `post_dopisac_update_card` | ✅ `pass` | ['✅ Zapisać', '➕ Dopisać', '❌ Anulować'] |
| `post_dopisac_card_is_duplicate_update` | ✅ `pass` | card text: 'Zaktualizować Oskar Stabilski (Wrocław) o:\nAdres: ul. Stabilna 7?' |
| `final_save_button_present` | ✅ `pass` | ✅ Zapisać |
| `final_save_confirmed` | ❌ `fail` | got 2 reply(ies); first: '✅ Dane zaktualizowane.' |
| `sheets_row_updated_with_new_address` | ✅ `pass` | row 71 matched |
| `sheets_row_updated_with_new_address_field_Adres` | ✅ `pass` | row['Adres']='ul. Stabilna 7' contains 'ul. Stabilna 7' |

<details><summary>Context</summary>

```
client_name: 'Oskar Stabilski'
client_city: 'Wrocław'
setup_email: 'e2e.test.222405.b11@e2e-noinbox.local'
new_address: 'ul. Stabilna 7'
setup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 676408040, e2e.test.222405.b11@e2e-noinbox.local, PV'
setup_co_dalej_closed: True
dup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 676408040, e2e.test.222405.b11@e2e-noinbox.local, PV'
reply_count: 1
post_dopisac_reply_count: 1
dopisac_text: 'adres: ul. Stabilna 7'
update_reply_count: 1
final_save_confirmed_replies: ['✅ Dane zaktualizowane.', 'Co dalej — Oskar Stabilski (Wrocław)? Spotkanie, telefon, mail, odłożyć na później?']
final_save_confirmed_co_dalej_closed: True
```
</details>

---
