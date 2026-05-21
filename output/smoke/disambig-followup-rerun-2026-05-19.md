# OZE-Agent E2E Report ✅

_Generated: 2026-05-19T20:29:40.098449+00:00_

**Overall:** PASS
**Scenarios:** 1 (pass 1, blocker 0)

**Check tag counts:** ✅ pass=4, ⚠️ known_drift=0, 🟡 expected_fail=0, ❌ fail=0, 🛑 blocker=0

## ✅ Clean PASS

## ✅ `show_client_multi_match_disambig` — PASS  _[read_only]_

- started: `2026-05-19T20:29:33.685097+00:00`
- ended:   `2026-05-19T20:29:40.096237+00:00` (6.4s)

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

---
