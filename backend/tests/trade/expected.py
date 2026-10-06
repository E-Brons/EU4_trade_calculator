"""What we currently expect of the calculation. This file is the RED -> GREEN ledger.

A stage listed "red" or "not_implemented" is verified as strict xfail: the moment its rule becomes correct the test
turns XPASS (= failure) and tells you to move it to "green". Nothing ever goes green silently, and a green stage can
never silently regress. Change an entry here only together with the calc.py change that justifies it.
"""

EXPECTED_STAGE_STATUS: dict[str, tuple[str, str]] = {
    "propagation": ("red", "R05: threshold + per-link truncation exact except 173 of 114,435: links with steer weight 0 do not propagate in start saves (cape_of_good_hope, california, ...) but do in played saves (gate rule open); MOR ship term in S80/U01"),
    "raw_power": ("red", "R06: observed per-country merchant power exact except 9 of 89,500: TMB/SCA without has_trader, VER rheinland +10, MKL north_sea +5 (U05), MNG canton -10 and BRU saxony +10 (U06)"),
    "multiplier": ("not_implemented", "R01/R02: max_demand is an observed input, not derived"),
    "val": ("green", ""),
    "transfers": ("red", "R04: exact in the 86 earlier saves; the Venice game (U14-U24, U27) has givers AVR and LDU that transfer their whole val (fraction ~1.0 instead of 0.5: a subject type the rule does not know yet)"),
    "retain_power": ("red", "R03 C-09: U05 gulf_of_aden keeps the power of AFA, which lost its last province after the monthly computation (stale aggregate, not a rule failure)"),
    "pull_power": ("red", "R03 final rule B: exact except U05 ethiopia (stale AFA aggregate, R03 C-09)"),
    "retention": ("green", ""),
    "current_value": ("red", "R08/R12: single-link nodes (zanzibar, australia) record outgoing 0 although retention < 1; an eligibility rule was tried and refuted (breaks lima)"),
    "steer_weights": ("red", "R08"),
    "link_flow": ("red", "R08 C-06 link identity with `add`: exact except U05 ethiopia->gulf_of_aden (keeps AFA's old add, stale aggregate R12 U-R12-2)"),
    "income_share": ("red", "fixed-point share rule exact except 14 entries at genua in S64 (R07 follow-up)"),
    "income_efficiency": ("red", "R07: 4 away collectors (MOR, AYU) in S79/S80 are 0.1-1% off: merchant-present bonus rule not settled"),
}

EXPECTED_CHAIN = "red"   # end-to-end calc.calculate vs every recorded node/collector value; green once all stages are

# Edge cases no fixture exhibits yet (strict: must equal the real uncovered set; shrink it by adding fixtures).
KNOWN_UNCOVERED: frozenset[str] = frozenset(
    {"EC-N07", "EC-N09", "EC-W02"} | {f"IV-{i:02d}" for i in range(1, 17)}
)
