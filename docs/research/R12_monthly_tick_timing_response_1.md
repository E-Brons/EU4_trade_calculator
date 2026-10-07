# R12 response 1 - Monthly tick timing

Only data-settled points. Scripts: `backend/scripts/research/r07_r08_r12_links.py`, `links2.py`, `links3.py`, `consist.py`, `prev.py`. Corpus: 82 saves (U01 = S80 and U02 = S79 in content).

## Q1 - The mismatch between `sum(downstream incoming.value)` and `outgoing`
Claim C-01 (confirmed in the tight form stated under Verification: `|sum(value) - sum(add) - outgoing x sum(w)| <= 0.001 x links` in 5,615 of 5,615 distinct nodes): the difference is explained by two effects, both visible in saved fields: (a) the steering bonus, `incoming.add` (ducats created on the link), and (b) the 3-decimal truncation of the node weights `steer_power` (their sum is 0.998, 0.999 or 1.000) and of the link values.
Source: 5,768 nodes with outgoing links in 82 saves. `|sum value - outgoing| <= 0.0015*links`: 4,834 nodes (83.8 % by this strict tolerance; 85.4 % of the 5,615 distinct nodes; the "95.5 %" quoted in the request was not reproduced: on the distinct nodes `|sum value - outgoing|` <= 0.01 holds in 94.1 %, <= 0.05 in 98.0 %, <= 0.5 % of outgoing in 96.3 %, <= 1 % in 97.0 %). 934 nodes differ more. `|sum value - sum add - outgoing| <= 0.0015*links`: 4,908. Every node (5,768 of 5,768) satisfies `|(sum value - sum add) - outgoing| <= outgoing*(1 - sum(w)) + 0.003*links + 0.001*outgoing*links`. Per link: `value - add` lies in `[outgoing*w - 0.002, outgoing*(w + 0.001) + 0.002]` in 12,113 of 12,113 links. Nodes with any non-zero link `add`: 224 (112 distinct). Quote of a mismatch without any `add`: S01 `canton` outgoing 5.278, downstream sum 5.271, sum add 0.0; S01 `hangzhou` 10.263 vs 10.251; weights sum 0.999 there.
Test using saved fields only: compute `sum(incoming.value) - sum(incoming.add)` and compare with `outgoing * sum(steer_power)`; equality within 0.002 per link.
Ruled out by the data: `value_added_outgoing != outgoing` (it equals `outgoing` in 5,768 of 5,768 nodes with links, tolerance 0.0005), as the request already says. One-tick lag, end-node and merchant-republic effects: no evidence needed to explain any node; not separately testable with one snapshot per save -> UNKNOWN.

## Q2 - `value_added_outgoing` and `add` (data part)
`value_added_outgoing == outgoing` in 5,768 of 5,768 nodes, also where links carry `add`; the steering bonus is only in `incoming.add` / `incoming.value` (see R08 response Q3, Q4). The draft's `value_added_outgoing = outgoing x (1 + steering_bonus)` is contradicted. `add` of a country = country strength divided by a node-dependent factor (R08 response Q2); `incoming.add = outgoing * w_L * sum(add of entries on link L)` in 12,111 of 12,113 links (the two others are explained by an entry with `add` but no `type`).

## Q3 - Validation with real rows
`current = (local_value + sum(incoming.value)) * retention` and `outgoing = gross - current` hold in the corpus (`consist.py`): start snapshots: current 5,608 of 5,636 (tolerance 0.0015), outgoing 4,914 of 4,914; ticked saves (S79, S80, U01, U02): 135 of 135 and 129 of 129; retention = retain/(retain+pull) 4,942 of 4,942 (start) and 129 of 129 (ticked) within 0.0011. The goal's example rows are not re-derived here (no script run for them).

## Q5 - Played saves not on the 1st
Claim C-02 (confirmed for the listed identities): the two played saves (dated 1665.4.22 and 1682.4.18) are internally consistent in the same way as the start snapshots: `val == trunc3(max_pow*max_demand)`: start 82,260 of 82,260; ticked 1,816 of 1,816. `retention`, `outgoing`, `current` identities: see Q3. `total == sum(val)` within 0.01: start 5,916 of 6,205, ticked 139 of 160 (lower in both; not explained). So the stored values of a mid-month save are from one consistent tick; which inputs changed since the last tick (merchant placement, ships, diplomacy) is UNKNOWN from the save alone.
Consistency check with saved fields only: val identity, retention identity, `current` identity and link identity above; a stale save would break the link identity (weights vs `incoming`), which holds in 12,113 of 12,113 links including the played saves.
Updated 2026-10-05: U04 (in-game date 1691.11.1, a tick day) satisfies the same identities as the mid-month saves, and U05 shows country entries updating at once while node aggregates keep the last monthly computation (section 'Update 2026-10-05', U-R12-2; inferred from one event).

## Q6 - `prev` timing
Claim C-03 (inferred): `prev` is computed from the province power that is in the same snapshot. Rule tested: `prev(country, node) = trunc3( sum over direct downstream nodes D with province_power_D >= 10 of province_power_D / 5 )`, `prev.py`: start snapshots 82,197 of 82,260 entries exact (0.077 % bad; with the per-link truncation `sum_D trunc3(p_D/5)` of R05 it is 82,207 of 82,260, 0.064 % bad), ticked saves 1,849 of 1,854 (0.27 % bad). A lag of one tick would make nearly all entries with changing province power inexact in ticked saves; it does not. The 5 ticked misses are all tag MOR in S80 (`kongo`, `katsina`, `cape_of_good_hope`, `brazil`, `timbuktu`): recorded prev 10.797 vs predicted 10.272 (and 12.305/11.78, 14.216/13.341), i.e. +0.525/+0.875: cause not identified (R05 Q3).

## Not answered (needs an outside source)
Q2 quotes/definition of `add`, Q4 day of month and order of the tick, Q6 quote check, Q7 define `NAV_PER_ADDED_SUB_NODE`. Not answered (analysis not finished): a test for value lag/end-node effects.

## Verification (date 2026-10-04)
Independent recomputation (new code): `backend/scripts/research/ver_common.py`, `ver_r12.py`, `ver_r12b.py`, `ver_r12c.py`. U01/U02 duplicate S80/S79 in trade content.

Re-run and matching: 5,768 nodes with links; 4,834 nodes within `0.0015 x links` (83.8 %); 4,908 after subtracting `add`; 934 beyond; `value_added_outgoing == outgoing` 5,768 of 5,768; loose bound 5,768 of 5,768; link bound 12,113 of 12,113; weight sums 24 / 1,535 / 4,209; the quoted rows S01 `canton` (5.278 vs 5.271) and `hangzhou` (10.263 vs 10.251, weights 0.333 x3 = 0.999, no `add`); `val == trunc3(max_pow x max_demand)` 82,260 / 82,260 and 1,816 / 1,816; `total == sum(val)` 5,916 of 6,205 and 139 of 160; `current` 5,608 of 5,636 and 135 of 135; `outgoing` 4,914 of 4,914 and 129 of 129; `retention` 4,942 of 4,942 and 129 of 129; `prev` 82,197 of 82,260 (one truncation of the sum) and 1,849 of 1,854; the five MOR misses in S80; dates 1665.4.22 and 1682.4.18.

Corrected / added:
- C-01 is confirmed in a tight form: `|sum(value) - sum(add) - outgoing x sum(w)| <= 0.001 x links` holds in 5,615 of 5,615 distinct nodes (5,503 without `add`, 112 with). The two effects (steering `add`, 3-decimal truncation of weights and values) therefore explain every node; the first version's loose bound had slack terms.
- The "95.5 %" of the request: not reproduced; on distinct nodes the match rate is 73.8 % (abs 0.001), 85.4 % (0.0015 x links), 94.1 % (abs 0.01), 98.0 % (abs 0.05), 96.3 % (0.5 % of outgoing), 97.0 % (1 %), 97.5 % (2 %).
- Counts over 82 saves double-count the played saves: 224 nodes with `add` -> 112 distinct; 5,768 nodes -> 5,615 distinct.
- `prev` with the per-link truncation `sum_D trunc3(p_D/5)` (R05 form) matches 82,207 of 82,260 start entries (not 82,197); the played misses are unchanged.
- The hand-computed `alexandria` example in Q3 was removed earlier (not from a script).

Could not be verified: the claim that a one-tick lag "would break many entries" (argument, not a count); Q4, Q7 and the other outside-source points.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below are single runs of `backend/scripts/research/u345_pipe_*.py` (own code; `u345_pipe_stages.py` runs the project's `verify_world`); they have not been independently re-computed, unlike the Verification section above. New data: U03 (in-game date 1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 1691.11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign (player TUR, game 1.37.5, 80 trade nodes) as S79 (1665.4.22) and S80 (1682.4.18); they are not independent samples. Counts refer to these saves unless stated otherwise.

### U-R12-1 Identities on the new saves (tick-day save U04)
Hold in all three saves (U03 / U04 / U05):
- `val == trunc3(max_pow x max_demand)`: 866/866, 869/869, 859/859.
- `current = (local_value + sum incoming.value) x retention`: 66/66, 66/66, 65/65; `outgoing = gross - current`: 63/63, 63/63, 62/62; `retention = retain / (retain + pull)` within 0.0011: 63/63, 63/63, 62/62.
- Link identities and the tight conservation bound: see the R08 update (77/77 nodes, 159/159 links each; one identity-2 exception in U05, below).
- Weight sums 1.0 / 0.999 / 0.998 and one node with 0.997 (U03).
- Strict `|sum value - outgoing| <= 0.0015 x links`: not recomputed on the new saves; `|sum value - sum add - out| <= 0.0015 x links` holds in 38/77, 39/77, 42/77 nodes with links (21/77, 22/77, 22/77 without subtracting `add`; 56, 55, 55 nodes carry a link `add`). These are rates over one played save and are not comparable with the corpus-wide 83.8% figure.
- U04 is on the 1st of the month and shows the same identity results as U03 (9th) and U05 (15th): there is no mid-month artefact in these identities.

### U-R12-2 Stale node fields after a country loses its last province (new; updates Q5)
In U05 (1693.4.15, not a 1st) the tag AFA is listed in `top_power` of `ethiopia` (value 2.61) and `gulf_of_aden` (7.518) but has no entry at those nodes (in U03 and U04 AFA has an entry at ethiopia: `type=1`, `steer_power=1`, `add=0.065`, `has_trader`, `max_pow=2.0`). The country AFA still exists but has no `num_of_cities` / `development` key in U05 (U04: `num_of_cities 1`, `development 5.0`): it lost its last province between the two saves. The node aggregates and the link value still contain its old power:
- `pull_power` of ethiopia recorded 247.475 vs calc 244.865: difference 2.610 = AFA's `top_power` value; `retain_power` of gulf_of_aden recorded 795.345 vs calc 787.827: difference 7.518 = AFA's `top_power` value there (the only two failures of these stages in U05).
- `max` of ethiopia and gulf_of_aden exceeds `p_pow` + the sum over present entries by exactly 2.0 and 7.0 (2.0 = AFA's last `max_pow` at ethiopia; the 7.0 at gulf_of_aden was not matched to an AFA field [second pass 2026-10-05: matched, see the Verification section below]).
- Link `ethiopia -> gulf_of_aden` has `incoming.add` 0.377 = 5.804 x 1.0 x 0.065 (AFA's `add` in U03/U04) although no entry at ethiopia carries an `add` any more.
Reading: per-country entries are updated at once when a country ceases to exist, while `top_power`, `max`, `pull_power`, `retain_power` and `incoming.add` keep the values of the last monthly computation. Confidence: confirmed as a description of this save (exact equalities); that the stale fields are the tick's is inferred (one event, one save; which day the tick ran is not identified by this save). UNKNOWN: when AFA lost its province; whether other mid-month changes (merchant recalled, ship moved) behave the same.

### U-R12-3 `prev` timing on the new saves (updates Q6)
The one-hop rule with per-link truncation and threshold 10 (ungated, candidates as in the R05 update) is exact in 959/963 (U03), 963/967 (U04), 951/955 (U05) candidates (S79 1055/1060, S80 967/976); the 4 misses per new save are the `polynesia_node` entries C02, C03, C12, HOL, not a timing effect (recorded `prev` 0 for all four). The tick-day save U04 behaves like the others, so no evidence of a one-tick lag appears (inferred).

### Updated UNKNOWN list (2026-10-05)
- Day of the month and order of the tick (needs a source); which stored fields are recomputed daily (entries, country existence) and which only at the tick (`top_power`, `max`, `pull_power`, `retain_power`, `incoming.add`) rests on one event.
- The definition behind the "95.5%" figure (not reproduced).

### Verification 2026-10-05 (second pass)

Method: new code `backend/scripts/research/ver2_c_stages.py` (project `verify_world` over all 85 manifest saves; U01/U02 are copies of S80/S79, so corpus-wide counts contain two duplicates), `ver2_c_identities.py` (own re-computation of the identities, prev rule, gate and ship-term counts from the parsed trade trees, exact decimal truncation), `ver2_c_gates.py`, `ver2_c_worst.py`.

Matched: `val` 866/866, 869/869, 859/859; `current` 66/66, 66/66, 65/65; `outgoing` 63/63, 63/63, 62/62; `retention` 63/63, 63/63, 62/62 (all 85 saves: `current` 6,075 of 6,103, the 28 misses are in start saves as before; `outgoing` 5,360 of 5,360; `retention` 5,388 of 5,388); link identities as in the R08 verification; `prev` rule 959/963, 963/967, 951/955 (the 4 misses per save are `polynesia_node` C02, C03, C12, HOL, where the gate is right); weight sums; AFA facts (no entry at `ethiopia` and `gulf_of_aden` in U05; U03/U04 entry at `ethiopia`: `type 1`, `steer_power 1`, `add 0.065`, `has_trader`, `max_pow 2.0`; `num_of_cities 1` / `development 5.0` in U04, both absent in U05).
Corrected: the open remark "the 7.0 at gulf_of_aden was not matched to an AFA field" - it is matched: AFA's U04 entry at its capital node `gulf_of_aden` has `max_pow 13.26` = `province_power 1.26` + 5 (`has_capital`) + 5 (`modifier` `merchants_too_succesful`, 24 days left in U04) + 2 (merchant constant); without the province and with the modifier expired that leaves 7.0, and the `top_power` values are 2.0 x 1.305 = 2.61 and 7.0 x 1.074 = 7.518 (AFA's U04 `max_demand` 1.293 and 1.062 plus 0.012; AFA has no entry in U05, so this cannot be read). Consequence for the reading of U-R12-2: the aggregates are not a copy of AFA's U04 entry; they were computed after AFA had lost its province, and the entry was removed after that computation (inferred from one event; the day of the computation stays UNKNOWN).
Label: the tick-day statements rest on one tick-day save (U04), see the R05 verification.
Unverifiable: day of the month and order of the tick (needs a source).

## Update 2026-10-05 - Venice series U07-U30 (timing)

Data: the Venice series U07-U30 (player VEN, game 1.37.5, non-Ironman plain-text saves, same mod list as S01, new campaign started 1444.11.11): U07 1444.11.11, U08 11.14, U09 11.30, U10 12.01, U11 12.02, U12 12.11, U13 12.31, U14 1445.01.01, U15 01.02, U16 01.15, U17 01.24, U18 01.30, U19 01.31, U20 02.01, U21 02.03, U22 02.10, U23 02.17, U24 02.28, U25 03.01 (U07-U25: no player action at all); then U26 03.31 (all three VEN merchants recalled during March), U27 04.01, U28 05.01 (ragusa merchant sent again), U29 06.01 (alexandria), U30 07.02 (wien). Scripts: `backend/scripts/research/venice_a_*.py` (loader `venice_load.py`), second pass `venice_a_ver.py` (raw text diff of the `trade` block, own Decimal loop for `prev`).

### V-R12-1 Computed trade values change only on the 1st of a month; between two 1sts only merchant placement changes
Claim: in a hands-off game every computed value of the `trade` block (`max_demand`, `val`, `max_pow`, `prev`, `province_power`, `power_fraction`, `total`, `money`, `add`, node `total`, `top_power`, `incoming`, `steer_power`, `retain_power`, `pull_power`, `trade_goods_size`) is identical in all saves of one month and changes at the 1st. The only trade-block fields that change between two 1sts are the merchant-placement flags of entries (`has_trader`, `type`, `steer_power` key of an entry) and the countdown `duration` of entry modifiers.
Applies when: all 24 saves; the first value change after the bookmark date happens at 1444.12.1 (U10), not earlier.
Source: `venice_a_fields.py` (parsed fields) and, independently, `venice_a_ver.py 1` (raw-text line diff of the `trade` block).
Quote (fields changed between consecutive saves; parser / changed text lines): U09 11.30 -> U10 12.01: 27,612 fields in 80 nodes / 43,797 lines (`max_demand` 19,074 fields, `val`, `max_pow`, `money`, `total`, `power_fraction`, `add`, `top_power`, `incoming`, `steer_power`); U13 -> U14 (1.1): 8,482 / 11,206; U19 -> U20 (2.1): 19,776 / 28,199; U24 -> U25 (3.1): 11,468 / 17,381; U26 -> U27 (4.1): 26,531 / 36,238; U27 -> U28 (5.1): 25,628 / 36,666; U28 -> U29 (6.1): 13,666 / 17,505; U29 -> U30 (6.1 -> 7.2): 11,292 / 13,951. Between 1sts: 3 to 626 fields (5 to 548 lines), every one in `has_trader` / `type` / `steer_power` / `modifier` (with `duration`): U07 -> U08 (11.11 -> 11.14) 106 fields (65 `has_trader`, 40 `type`, 1 `steer_power`), U08 -> U09 626, U10 -> U11 24, U11 -> U12 160, U12 -> U13 122, U14 -> U15 8, U15 -> U16 25, U16 -> U17 6, U17 -> U18 3, U18 -> U19 3, U20 -> U21 3, U21 -> U22 4, U22 -> U23 4, U23 -> U24 3, U25 -> U26 10.
Confidence: confirmed (two independent methods, 24 saves).
Caveats: the saves have one-day resolution and are taken at the 1st or later; whether the recomputation happens at 00:00 of the 1st or during that day cannot be seen (the save of the 1st already contains it). U30 (07.02) contains the July recomputation; whether it ran on 07.01 or 07.02 is not visible.

### V-R12-2 Stored identities hold on every day, including mid-month and after a merchant recall
Claim: the identities of the earlier rounds (`retention`, `current`, `outgoing`, `value_added_outgoing`, `val`, `power_fraction`, entry `total`, link value) hold exactly in all 24 saves, i.e. a mid-month save is not internally inconsistent: it is a consistent copy of the last computation, with only the placement flags moved on.
Source: `venice_a_identities.py` (integer thousandths).
Quote (totals over the 24 saves): `retention = ceil3(retain/(retain+pull))` 1,920/1,920; `current = ceil3(gross x retention)` 1,728/1,728 and `current = gross` for nodes with links and all weights 0: 192/192; `outgoing = gross - current` 1,920/1,920; `value_added_outgoing == outgoing` 1,584/1,584; `val = trunc3(max_pow x max_demand)` 34,681/34,681; `power_fraction = trunc3(eff / retain_power)` 16,406/16,406; `total = trunc3(current x power_fraction)` 16,406/16,406; link `value - add` within `[outgoing x w, outgoing x (w + 0.001)]` (+-0.002): 3,816/3,816. U26 (03.31, three merchants recalled since the last tick) satisfies all of them.
Confidence: confirmed.
Caveats: saves in which a country lost its last province between ticks (U05 AFA) are not in this series.

### V-R12-3 Which inputs act at once and which wait for the tick
Claim: (a) merchant placement (`has_trader`, `type`, `steer_power` key of the entry), the country field `transfer_home_bonus` (U26) and the node modifier `merchant_recalled` (appears at once, see R06 V-R06-3) are updated at once; (b) all numbers derived from them (`max_pow`, `val`, `add`, weights, `total`, `money`) stay at the last 1st value until the next 1st. Example: U26 (03.31): the three VEN entries at `alexandria`, `ragusa`, `wien` have lost `has_trader` and `type` but still carry `add` 0.071, `max_pow` 27.941 / 46.539 / 21.941 and the pre-recall weights [0.385, 0.339, 0.274] / [0.265, 0.614, 0.119] / [0.297, 0.448, 0.254]; U27 (04.01) has `max_pow` 25.948 / 44.565 / 19.948, no `add`, weights [0.521, 0.107, 0.37] / [0.582, 0.155, 0.261] / [0.144, 0.545, 0.309].
Source: `venice_a_fields.py`; rows of the recall from `venice_a_r06b.py` (second block of its output).
Confidence: confirmed for merchants; `transfer_home_bonus` is treated in R09. Inputs not varied in this series (ships, ideas, diplomacy, a country losing its last province) stay UNKNOWN.

### V-R12-4 Stale node aggregates (AFA, U05) are the normal mid-month state
Claim: since all node values are frozen between 1sts, a country whose entry disappears between two 1sts (U05 AFA) leaves its power in the node aggregates and link `add` until the next 1st: the AFA case is the ordinary behaviour, not an anomaly. Confidence: inferred (mechanism confirmed by V-R12-1/2; the AFA instance itself was not followed to the next tick).

### V-R12-5 The 4.5 % of nodes whose link values do not sum to `outgoing`
Not a timing effect: V-R12-2 shows the link identity exact in all 24 saves at every date; the sum deviation is the link bonus `add` plus 3-decimal truncation of the weights (R08 C-06, C-08).

### Verification 2026-10-05 (second pass)
V-R12-1 was recomputed with a different method (`venice_a_ver.py 1`: multiset difference of the raw text lines of the `trade` block, key names taken from the line text, not from the parser): same split (1sts: tens of thousands of lines, dominated by `max_demand`; other days: 5 to 548 lines in `has_trader`, `type`, `steer_power`, `duration`, `key`, `power`, `power_modifier`). V-R12-2 uses the project-independent integer-thousandths code of the R12 round (`final_r12_identities.py` logic re-implemented in `venice_a_identities.py`).

## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R12-1 C-06 of the final is now observed
Claim (E21): a country that loses its last province between two 1sts (NAX, 1444.12.01) keeps its `top_power` rows (alexandria 2.046, constantinople 9.579) on 12.03 and 12.15 and loses them at 1445.01.01. The final's C-06 (inferred) is confirmed for `top_power`.

### V2-R12-2 Province inputs that wait longer than one tick
Claim: a mercantilism change (E12) and an autonomy change (E18) made on 1444.12.01 do not show in the province `trade_power` on 1445.01.01, only on 1445.02.01 (R13), while a building (E17) and a province trade-power modifier (E09) show at once. On which days a province's stored `trade_power` is recomputed is R13's open question (E23, a save every 2nd day 1444.12.03-1445.01.02, is pending).
