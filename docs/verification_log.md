# Verification log

One row per run of `scripts/verify_all.sh` in CI (appended by `backend/scripts/verification_log.py`, committed by the
`verify-trade-calculation` job). Data: the clean saves of `datasets/eu4/` (reports excluded). Each stage cell is
`not exact / outside 5% / checks`; the CI bar is "outside 5%" = 0 for every stage and every save end to end.

| date (UTC) | commit | calc | saves | reproduced exactly | reproduced within 5% | propagation | raw_power | multiplier | val | transfers | retain_power | pull_power | retention | current_value | steer_weights | steering_bonus | link_flow | income_share | income_efficiency |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-10-09 15:38 | cfa8814e | 0.3.0 | 205 | 5 | 18 | 2 / 2 / 400691 | 109 / 106 / 296534 | n/a | 0 / 0 / 296148 | 0 / 0 / 9416 | 14 / 3 / 16400 | 66 / 30 / 13945 | 0 / 0 / 16400 | 0 / 0 / 31090 | 2099 / 157 / 32595 | 838 / 272 / 19084 | 55 / 4 / 29130 | 0 / 0 / 261228 | 71 / 14 / 6260 |
