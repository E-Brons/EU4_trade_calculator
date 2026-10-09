# Verification log

One row per run of `scripts/verify_all.sh` in CI (appended by `backend/scripts/verification_log.py`, committed by the
`verify-trade-calculation` job). Data: the clean saves of `datasets/eu4/` (reports excluded). Each stage cell is
`not exact / outside 5% / checks`; the CI bar is "outside 5%" = 0 for every stage and every save end to end.

| date (UTC) | commit | calc | saves | reproduced exactly | reproduced within 5% | propagation | raw_power | multiplier | val | transfers | retain_power | pull_power | retention | current_value | steer_weights | steering_bonus | link_flow | income_share | income_efficiency |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
