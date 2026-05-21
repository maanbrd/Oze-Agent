# OZE-Agent E2E Report ❌

_Generated: 2026-05-19T20:20:44.230828+00:00_

**Overall:** FAIL
**Scenarios:** 1 (pass 0, blocker 0)

**Check tag counts:** ✅ pass=5, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=1, 🛑 blocker=0

## ❌ Fails

## ❌ `add_client_dup_dopisac_update_path` — FAIL  _[mutating_core]_

- started: `2026-05-19T20:19:37.319032+00:00`
- ended:   `2026-05-19T20:20:44.225882+00:00` (66.9s)

| Check | Tag | Detail |
|---|---|---|
| `setup_client_created` | ✅ `pass` | client 'Oskar Stabilski' setup OK |
| `setup_sheets_row_ready` | ✅ `pass` | row 71 matched |
| `setup_sheets_row_ready_field_Telefon` | ✅ `pass` | row['Telefon']='651422656' contains '651422656' |
| `setup_sheets_row_ready_field_Email` | ✅ `pass` | row['Email']='e2e.test.221937.b11@e2e-noinbox.local' contains 'e2e.test.221937.b11@e2e-noinbox.local' |
| `got_dup_card` | ✅ `pass` | ['📋 Dopisz do istniejącego', '➕ Utwórz nowy wpis'] |
| `duplicate_update_card_detected` | ❌ `fail` | card text: '⚠️ Masz już Oskar Stabilski (Wrocław, PV).\nDodać nowego czy dopisać do istniejącego?' |

<details><summary>Context</summary>

```
client_name: 'Oskar Stabilski'
client_city: 'Wrocław'
setup_email: 'e2e.test.221937.b11@e2e-noinbox.local'
new_email: 'updated-e2e.test.221937.b11@e2e-noinbox.local'
setup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 651422656, e2e.test.221937.b11@e2e-noinbox.local, PV'
setup_co_dalej_closed: True
dup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 651422656, PV, updated-e2e.test.221937.b11@e2e-noinbox.local'
reply_count: 1
```
</details>

---
