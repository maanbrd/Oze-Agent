# OZE-Agent E2E Report 🛑

_Generated: 2026-05-19T20:22:52.742986+00:00_

**Overall:** BLOCKER
**Scenarios:** 1 (pass 0, blocker 1)

**Check tag counts:** ✅ pass=0, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=0, 🛑 blocker=1

## 🛑 Blockers

## 🛑 `add_client_dup_dopisac_update_path` — BLOCKER  _[mutating_core]_

- started: `2026-05-19T20:22:27.095364+00:00`
- ended:   `2026-05-19T20:22:52.739694+00:00` (25.6s)

| Check | Tag | Detail |
|---|---|---|
| `setup_save_confirmed` | 🛑 `blocker` | setup save reply lacks confirm marker; got ['✅ Dane zaktualizowane.', 'Co dalej — Oskar Stabilski (Wrocław)? Spotkanie, telefon, mail, odłożyć na późni'] |

<details><summary>Context</summary>

```
client_name: 'Oskar Stabilski'
client_city: 'Wrocław'
setup_email: 'e2e.test.222227.b11@e2e-noinbox.local'
new_address: 'ul. Stabilna 7'
setup_trigger: 'dodaj klienta Oskar Stabilski, Wrocław, 641274577, e2e.test.222227.b11@e2e-noinbox.local, PV'
```
</details>

---
