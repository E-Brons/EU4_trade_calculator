# R12 final - Order and timing of the monthly trade tick versus the values stored in a save

Status: FINAL (2026-10-05). Merged from `R12_monthly_tick_timing_draft.md` (the draft's step list), `R12_monthly_tick_timing_response_1.md` (whole-corpus identities, stale aggregates, U03-U05) and the controlled game of the Venice series U07-U30 (24 saves, `response_1` section 'Update 2026-10-05 - Venice series'). The topic is closed by the saves alone: no outside source was consulted and none is needed for the calculator. What a save cannot show (the order of the steps inside the 1st) is listed in section 5 and is not needed to reproduce the stored numbers.

Scripts (from `backend/`): `scripts/research/venice_a_fields.py` (fields that change between consecutive saves), `venice_a_ver.py 1` (same question on raw text lines, independent), `venice_a_identities.py` (node and link identities, integer thousandths), `venice_a_r06b.py`, `venice_a_thb.py` (merchant and country-field timeline). Loader: `venice_load.py`. Earlier whole-corpus scripts: `final_r12_identities.py`, `final_r12_stale.py`.

## 1. Answer

```
# game 1.37.5, state of one trade block as stored in a save

monthly computation ("tick"): runs once per month and is contained in every save dated the 1st of the month or later in that month
    recomputed: province_power, ship_power, prev, max_pow (incl. the merchant term R, see R06), max_demand, val, t_in/t_out,
                power_fraction, retain_power, pull_power, retention, current, outgoing, value_added_outgoing, local_value, trade_goods_size,
                total/money of collectors, steer_power weights, link incoming.value and incoming.add, top_power(+values), node total/p_pow/max
    the bookmark state (1444.11.11, saved before any tick) is NOT a tick result

between two ticks only these change in the trade block, at once:
    entry flags  has_trader, type, the steer_power key of an entry      (merchant placement by the player or the AI)
    entry modifier list and its duration countdown (merchant_recalled: duration 3650, minus 1 per day, R06)
    (country fields such as transfer_home_bonus change at once too: 0.3 -> 0.0 when the three merchants were recalled, 0.1 per steering merchant)
all numbers derived from them wait for the next 1st.

consequence for a save written on day d of a month:
    computed values  = result of the computation on the 1st of that month (tick day: the save already contains it)
    merchant flags, modifiers, country fields = state on day d
    stored identities (retention, current, outgoing, val, power_fraction, total, link value) hold exactly on every day
```

## 2. Variables

```json
[
 {"id": "tick_day", "meaning": "day of the month on which the stored trade values are recomputed", "unit": "day", "kind": "constant", "source": {"type": "save", "path": "Venice series U07-U30"}, "confidence": "confirmed (1st)"},
 {"id": "entry_flags", "meaning": "has_trader / type / steer_power key: merchant placement, current on the save day", "unit": "flag", "kind": "read", "source": {"type": "save", "path": "trade.node[].<TAG>"}, "confidence": "confirmed"},
 {"id": "computed_values", "meaning": "all other trade-block numbers: equal to the last 1st's computation", "unit": "ducats/power", "kind": "read", "source": {"type": "save", "path": "trade.node[]"}, "confidence": "confirmed"}
]
```

## 3. Claims

### C-01 Computed values change only on the 1st
Claim: in a hands-off game no computed trade value changes between two 1sts. Changes between consecutive saves (parser / raw text lines): 1444.11.30 -> 12.01 27,612 fields in 80 nodes / 43,797 lines (`max_demand` 19,074 fields); 1444.12.31 -> 1445.1.1 8,482 / 11,206; 1445.1.31 -> 2.1 19,776 / 28,199; 2.28 -> 3.1 11,468 / 17,381; 3.31 -> 4.1 26,531 / 36,238; 4.1 -> 5.1 25,628 / 36,666; 5.1 -> 6.1 13,666 / 17,505; 6.1 -> 7.2 11,292 / 13,951. Between 1sts: 3-626 fields (5-548 lines), all in `has_trader`, `type`, `steer_power`, entry `modifier`/`duration`. Source: Venice series U07-U30, `venice_a_fields.py`, independently `venice_a_ver.py 1`. Confidence: confirmed.

### C-02 A mid-month save is consistent
Claim: all stored identities hold exactly in all 24 saves, including mid-month days and the save taken after a merchant recall (U26): `retention` 1,920/1,920, `current` (1,728 + 192)/(1,728 + 192), `outgoing` 1,920/1,920, `value_added_outgoing == outgoing` 1,584/1,584, `val = trunc3(max_pow x max_demand)` 34,681/34,681, `power_fraction` 16,406/16,406, `total = trunc3(current x power_fraction)` 16,406/16,406, link `value - add` within `[outgoing x w, outgoing x (w + 0.001)]` 3,816/3,816. Earlier corpus: same identities in the start, played and U03-U05 saves. Source: `venice_a_identities.py`. Confidence: confirmed.

### C-03 No one-tick lag inside a month
Claim: `prev` and the other derived values of a save are computed from the values of the same monthly computation (`prev` from the same save's `province_power`: R05). Refuted alternative: values from the previous month (the previous-month weight gate fails from the second 1st on, R05 V-R05-1). Confidence: confirmed for `prev`, identities and `province_power` on a 1st.

### C-04 The bookmark state is not a tick result
Claim: in the saves 1444.11.11-11.30 (U07-U09) the merchant term R of `max_pow` is 0 for all 2,401 merchant-entry rows, the stored `prev` follows the bookmark weights and `transfer_home_bonus` is 0.0 at the bookmark save and 0.3 three days later; everything else that depends on merchants (R, `add`, weights) is first computed on 1444.12.1. Source: R06 V-R06-1, R05 V-R05-1, `venice_a_thb.py`. Confidence: confirmed. This is why every start snapshot (saved before any tick) differs from a played save; it is not a different game mode.

### C-05 Inputs that act at once and inputs that wait
Claim: merchant placement flags, node modifiers (`merchant_recalled`) and country fields such as `transfer_home_bonus` are current on the save day; `max_pow` (incl. R and the -10 of `merchant_recalled`), `add`, weights and everything downstream wait for the next 1st: U26 (03.31) has lost the merchants' `has_trader`/`type` flags but keeps `add` 0.071, `max_pow` 27.941 / 46.539 / 21.941 and the old weights; U27 (04.01) has `max_pow` 25.948 / 44.565 / 19.948, no `add` and weights [0.521, 0.107, 0.37] / [0.582, 0.155, 0.261] / [0.144, 0.545, 0.309] at `alexandria` / `ragusa` / `wien`. Merchants that arrive mid-month have R = 0 until the next 1st (all 2 / 8 / 11 / 4 cases in U11 / U12 / U13 / U16), those that leave keep R (U26: 4 of 4). Confidence: confirmed for merchants (one country, plus the AI merchants of the game); not varied: ships, ideas, diplomacy (section 5).

### C-06 Stale node aggregates (AFA, U05) follow from C-01
Claim: a country that disappears between two 1sts leaves its power in `top_power`, `max`, `pull_power`, `retain_power` and the link `incoming.add` until the next 1st; this is the ordinary mid-month state (R03 C-09). Confidence: inferred (mechanism confirmed by C-01, the instance itself was not followed to the next 1st).

### C-07 The 4.5 % of nodes whose downstream link values do not sum to `outgoing` is not a timing effect
Claim: the link identity is exact in every save of the series on every day; the deviation is the steering bonus `add` plus 3-decimal truncation of weights (R08 C-06, C-08). Confidence: confirmed.

## 4. Validation against the data

| Check | Result |
|---|---|
| computed fields change only on the 1st | 24 saves, 23 consecutive pairs, two methods |
| all node and link identities, every day | exact in 24/24 saves |
| gate/`prev` on a 1st | exact with the right weights (R05) |
| `province_power` = controlled-province sum | 100 % on the 1sts (773/773, 772/772), 63-98 % between (R13 V-R13-1) |

## 5. Unknowns, contradictions between sources, and what would settle them

- The order of the steps inside the 1st (power -> propagation -> classification -> flow -> income): not observable in a save; the stored identities fix the dependency order (`val` -> `prev` inputs -> `retain`/`pull` -> `retention` -> `current` -> `outgoing` -> `total`/`money`) and this is all a calculator needs.
- Whether the computation runs at 00:00 of the 1st or later on it, and whether the 7 entries that had lost `has_trader` by the save of 1444.12.1 but carry R = 2 (R06 V-R06-2) show a different order of merchant moves and computation on that day: not visible with one save per day.
- Inputs not varied: ship assignment, ideas, diplomacy, a country losing its last province (R12 request_2 keeps these rows as data requests; they are not needed for the rule above).
- The "95.5 %" of the goal: not reproduced; the figure depends on a tolerance the goal does not give. The correct statement is C-07.
- Removed: the draft's 7-step daily/monthly schedule, and the goal's hypothesis that a mid-month save may be inconsistent by design (both unsupported by any save).

## 6. Sources (ranked)

Saves only: Venice series U07-U30 (controlled, two independent methods), S01-S80 and U01-U06 (whole-corpus identities, R12 response_1). No outside source consulted.

## 7. Provenance

Draft (2026-10-04) -> response_1 (saves only, verified) -> Update and second pass (U03-U05) -> this final after the Venice series (2026-10-05). Second-pass verification: `venice_a_ver.py` (raw text), `venice_a_identities.py` (independent integer code).

## 8. Rejected claims

- "The draft's 4.5 % mismatch is caused by `value_added_outgoing != outgoing`": refuted (equal in 5,768/5,768 nodes plus 1,584/1,584 here).
- "A save written on a non-tick day is inconsistent by design": refuted (C-02).
- "The played saves fail the weight gate because they are not written on a tick day": refuted by U04 (R05) and explained by C-04 / R05 V-R05-1.

## 9. Disposition of request_2

| Point | Disposition |
|---|---|
| Q1 day and order of the tick, quoted source | day settled from the saves (C-01); order not observable, not needed; a quote would only corroborate |
| Q2 definition of `value_added_outgoing` / `add` | R08 (equal to `outgoing`; `add` = link bonus, C-06) |
| Q3 `prev` timing quote | R05 (same-tick province power, C-03) |
| Q4 unverifiable defines and quotes | not needed for the calculation; removed with the draft claims |
| Q5 fixed-point truncation | R08 C-06 (3-decimal truncation, verified on 12,113 links) |
| Data rows | removed from request_2 (closed): 58 nodes -> R10; 95.5 % dropped; inputs not varied listed in section 5 as optional evidence |
