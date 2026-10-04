# R08 response 1 - Steering, link split, `add`

Answers only the points the fixture saves can settle (82 entries: S01-S80 + U01/U02; U01 = S80 and U02 = S79 in content, so there are only 2 independent played saves). Scripts: `backend/scripts/research/r07_r08_r12_*.py` (load, steer1-5, links, links2, links3, consist). Source for every claim below = the save corpus + the named script; the quoted rows are save fields (`node`, `tag`, key=value).

Corpus facts that frame everything:
- Start snapshots (S01-S78) contain **no `add` key at all** (0 entries); the 4 played-save files contain 1,222 entries with `type`+`add` (1,208 of them with a `val`; 611 distinct entries, since U01/U02 are copies) and 2 with `add` but no `type` (1 distinct). In start snapshots 3,300 of 3,576 nodes with a `type` entry and >= 2 links have exactly equal weights (1/N) (the denominator 3,934 first written here could not be reproduced): the stored `steer_power` weights there are not the result of steering. Only S79/S80 (U02/U01) can test a weight rule (105 node instances with steerers).

## Q1 - Rule for the node `steer_power` weights: NOT SETTLED (UNKNOWN), partial structure found

Claim C-01 (inferred, negative; rests on the two named nodes, not a corpus-wide count): non-steering / passive power is not part of the weights.
Applies when: played saves. Source: S80 `ohio` (links chesapeake_bay, st_lawrence; stored steer_power [0.0, 1.0]). Quote: `C04 {val: 49.625, t_out: 24.762}` (val - t_out = 24.863) is a puller that collects downstream at `chesapeake_bay` (link 0, `total 1.554`) (`r07_r08_r12_steer2.py`), yet weight 0 = 0.0; the three steerers GBR, C05, C10 all have `steer_power=1`. Also S80 `alexandria`: stored [0.715, 0.0, 0.284] although PAP (`steer_power=1`, val 44.251) and BLG (`steer_power=1`, val 12.844) are in link 1: weight 0.0. So entries with `steer_power` but no `type` are not counted in the weights; the draft's and our current `rule_steer_weights` (all non-collectors) is contradicted.

Claim C-02 (confirmed, negative): the plain share of steerers' `val` (or of `val - t_out + t_in`) does not reproduce the weights.
Source: `r07_r08_r12_steer1.py` / `steer3.py`, S79+S80, 105 node instances with >= 1 steerer and outgoing > 0, tolerance 0.0011 per weight: `val` exact in 28, `eff = val - t_out + t_in` exact in 29 (26 of the 105 are trivial single-link nodes; among the 79 nodes whose steerers use >= 2 links, plain `eff` is exact in only 3); `max_pow` exact in 26 of 105. (The figures `48 (eff) / 46 (val) of 222` for `type|steer_power` entries and `max_pow 52` in the first version were counts over the 4 files incl. the U01/U02 copies and nodes without steerers.) Powers of eff (0.9-1.3), additive constants and a ship weight did not help (best RMSE 0.040 vs 0.042).

Claim C-03 (inferred, not settled): weight of link L is proportional to `sum over steerers on L of eff_c * a_c`, where a_c is a country-level steering strength that is the largest `add` the country shows in that save (see Q2).
Evidence (unfitted, `r07_r08_r12_steer4.py` + clean subset test): nodes in which every steerer's `add` equals its country's largest `add` in the save (so a_c = own `add`): S79 9 of 10 nodes within 0.0011 for `eff*add` vs 7 of 10 for `val*add` vs 8 of 10 for `eff`; S80 6 of 11 vs 6 vs 5 (RMSE 0.0066 vs 0.0325 for plain eff). Quote (S79 `james_bay`, C05 eff 69.112 add 0.082 link 0; C07 eff 1.323 add 0.054 link 1): predicted [0.9876, 0.0124], stored [0.987, 0.012]. S80 `persia` (RUS eff 243.48 add 0.085 link 1; IRQ eff 4.221 add 0.061 link 0): predicted [0.0123, 0.9877], stored [0.012, 0.987]. Plain eff would give 0.0188 and 0.0170 for the small link.
Failures of the clean subset: S80 `california` (pred 0.9015/0.0985, stored 0.885/0.114), `mississippi_river` (0.0979 vs 0.084), `lahore` (0.6325 vs 0.631), `alexandria` (0.713 vs 0.715), `gujarat` (S79 0.5341 vs 0.516). Unfitted over all S79+S80 steerer nodes with a_c = largest `add`: 40 of 105 exact (RMSE 0.0227 as first reported with a default strength 0.05 for countries without an `add`; 0.0291 with strength 0 for them).
The goal's Example 1 (S79 `alexandria`) is not claimed: it was only reproduced by hand with an assumed strength for BLG, so it is left out as evidence.
A per-country fit of a_c over integer multiples of the observed adds (`steer5.py`) reaches 50 of 53 (S79) and 48 of 52 (S80) nodes within 0.004, but it has ~100 free parameters and is not a test; it is not used as evidence.
What would settle it: the country modifier `trade_steering` (not in the save) or an intervention pair changing only one steerer's modifier.

Claim about `trade_steering`: the save stores no such modifier (0 occurrences of `steering` in the S80 gamestate text, 58.7 MB).

## Q2 - What determines `add` : partial
Claim C-04 (confirmed): a steering entry's `add` is a country-level value divided by a small factor k that varies by node. Source: S80 multisets of `add` per country (`r07_r08_r12_steer1` listing): GBR 0.097 x9; TUR 0.101 x4; C05 {0.084 x2, 0.042 x4, 0.021 x1, 0.016 x1}; SUN {0.088 x2, 0.044 x2, 0.029, 0.022 x3}; SPA {0.057 x5, 0.028 x2, 0.019}; C03 {0.082 x3, 0.041 x3}. k = largest/own is ~1, 2, 3, 4, (5.25 for C05 `carribean_trade`, 0.016 vs 0.084): not always an integer.
What k depends on: tested and refuted as the sole driver (S80, C05 and SUN): the target node (C05 steers to `st_lawrence` with k = 1 at `james_bay`, 2 at `ohio` and `chesapeake_bay`), link index, number of links, number of steerers in the node, `val`, `t_out`. Not found: UNKNOWN. A merchant count per chain was tried for SUN (chengdu k1, burma k2, nippon k2, girin k3, gulf_of_siam/canton/hangzhou k4) and does not fit.
Claim C-05 (confirmed): the presence of the `add` key, not of `type`, marks a steering contribution to the link bonus: S80 `carribean_trade` entry `SCA {val: 31.654, add: 0.05, t_in: 10.772}` has no `type` and no `has_trader`, and it is needed to explain the link (see Q3). The draft's merchant-rank tier list (5 / 2.5 / 1.6 / 1.2 %) is contradicted: TUR has the same 0.101 in nodes with val 189 and 619.

## Q3 - Link-value identity: confirmed
Claim C-06 (confirmed): for every outgoing link L: `incoming.value = outgoing * w_L + incoming.add` and `incoming.add = outgoing * w_L * (sum of add over entries with an add key and steer link L)`.
Source: `r07_r08_r12_links2.py`, `links3.py`, all 82 saves, 5,768 nodes with links, 12,113 links. Identity 1: `outgoing*w_L - 0.002 <= value - add <= outgoing*(w_L + 0.001) + 0.002` holds in 12,113 of 12,113 links (weights are 3-decimal truncated, values too). Identity 2 (with the same truncation bounds plus the rounding of each `add`): 12,113 of 12,113 when all entries with an `add` key are summed, 12,111 when only entries with `type` are summed; the 2 failures of the latter are S80 and U01 `carribean_trade` link 0 (51.163 x 0.365 x 0.148 = 2.764 vs stored 3.697); including SCA's 0.05: 51.163 x 0.365 x 0.198 = 3.698, stored 3.697.
Rows (S79, the goal's examples; `alexandria` outgoing 25.551, w [0.648, 0.085, 0.266]): link 0 constantinople: 25.551 x 0.648 = 16.557, sum add .133 -> 2.202, value 18.759 (stored 18.759/2.202). Link 1 venice: 2.172, .117 -> 0.254, stored 2.425/0.254 (2.172 + 0.254 = 2.426). Link 2 genua: 6.797, .097 -> 0.659, stored 7.455/0.659. `gulf_of_aden` outgoing 16.981, w [0.217, 0.746, 0.036]: zanzibar 3.685, .165 -> 0.608 (stored 0.607, value 4.291), alexandria 12.668, .092 -> 1.165 (13.832), hormuz 0.611, .125 -> 0.076 (0.687).
Base of the percentage is the link's share of `outgoing` (not gross); the bonus is added to the downstream node's `incoming.value` (so it enters the downstream `current` formula), not to the steering country's income.

## Q4 - Conservation and `value_added_outgoing`
Claim C-07 (confirmed): `value_added_outgoing == outgoing` (tolerance 0.0005) in 5,768 of 5,768 nodes with links, including the 224 nodes (112 distinct) where a link carries a non-zero `add`. So the field does not contain the steering bonus; the draft's "amplified by merchant steering bonuses" is contradicted. Its meaning when it differs from `outgoing`: no instance in the corpus -> UNKNOWN.
Claim C-08 (confirmed): `sum(downstream incoming.value) = outgoing + sum(incoming.add)` up to weight truncation: in all 5,768 nodes `|(sum value - sum add) - outgoing| <= outgoing*(1 - sum(w)) + 0.003*links + 0.001*outgoing*links` (`links2.py`). Only 4,834 nodes satisfy `|sum value - outgoing| <= 0.0015*links`, 4,908 satisfy `|sum value - outgoing - sum add| <= 0.0015*links`; the rest is the truncation of the weights (see Q5). See the R12 response for the "4.5 %" statement.

## Q5 - Nobody steers / sum of weights
Sum of stored weights over the 5,768 nodes with links: 0.998 in 24, 0.999 in 1,535, 1.000 in 4,209 (nothing else; distinct saves: 12, 1,467, 4,136): weights are truncated to 3 decimals, which explains 0.999.
Nodes with >= 2 links and no `type`/`add` entry (`steer` script, stats): start snapshots: outgoing > 0: 299 equal weights, 127 all on the first link, 176 other; played saves: 8 equal, 4 all on first link, 0 other (4, 2, 0 distinct). A pull-direction model (passive countries weighted towards the link that leads to where they collect) explained 77 (unique links) to 198 (first link) of 602 start nodes: no rule found -> UNKNOWN; fixture nodes to inspect: S14 `patagonia` [1.0, 0.0], `mexico` [0.0, 1.0, 0.0], `california` [0, 1, 0, 0] (no steerers, uneven weights).

## Not answered (needs an outside source)
Q2 game rule with `TRADE_ADDED_VALUE_MODIFER` quote; Q6 existence/definition of `trade_steering` in game files; source of the tier list and of the `defines.lua` quote; wiki quotes. Not answered (analysis not finished): a rule for k in Q2; a complete rule for Q1.

## Verification (date 2026-10-04)
Independent recomputation (new code): `backend/scripts/research/ver_common.py`, `ver_r12.py`, `ver_r08.py`, `ver_r08b.py`, `ver_r08c.py`, `ver_r08d.py`. U01/U02 duplicate S80/S79 in trade content; distinct counts are given where they differ.

Re-run and matching:
- Link identities: identity 1 in 12,113 of 12,113 links, `value_added_outgoing == outgoing` in 5,768 of 5,768 nodes, weight sums 0.998 / 0.999 / 1.000 in 24 / 1,535 / 4,209 nodes.
- Example rows S79 `alexandria` (18.759 / 2.202, 2.425 / 0.254, 7.455 / 0.659; sums of `add` .133 / .117 / .097) and `gulf_of_aden` (4.291 / 0.607, 13.832 / 1.165, 0.687 / 0.076; sums .165 / .092 / .125), and the products outgoing x w.
- Plain-share weight rule: 105 node instances, `val` exact 28, `eff` exact 29.
- C-03: clean subset S79 9 of 10 (`eff x add`) vs 7 (`val x add`) vs 8 (`eff`); S80 6 of 11 vs 6 vs 5; S80 per-node max-error RMSE 0.0066 vs 0.0325; 40 of 105 over all steerer nodes; the quoted hits (`james_bay`, `persia`) and misses (`california`, `mississippi_river`, `lahore`, `alexandria`, `gujarat`) reproduce.
- C-04: the six `add` multisets of S80, TUR 0.101 in nodes with val 189, 290, 619 and 205, C05 targets (`st_lawrence` from `james_bay`, `ohio`, `chesapeake_bay`), SCA row at `carribean_trade`, start-snapshot counts for nodes without `type`/`add` entry (299 / 127 / 176), zero occurrences of `steering` in the S80 gamestate (58.7 MB).

Corrected:
- `type`+`add` entries: 1,208 -> 1,222 (1,208 is the number that also has a `val`); 611 distinct.
- Start snapshots, equal weights: "3,300 of 3,934" -> 3,300 of 3,576 (nodes with a `type` entry and >= 2 links); the 3,934 denominator could not be reproduced.
- C-01 quote `C04 {val: 24.9}`: the save has `val 49.625`, `t_out 24.762` (val - t_out = 24.863).
- C-02: `max_pow` 52 -> 26 of 105 (52 was the 4-file count); the "48 / 46 of 222" figures are 4-file counts; added that 26 of the 105 are trivial single-link nodes and plain `eff` is exact in only 3 of the other 79.
- Identity 2: 12,113 of 12,113 when every entry with an `add` key is summed; 12,111 is the count with `type` entries only.
- "224 nodes" with non-zero `add` -> 112 distinct; weight-sum counts and the Q5 played-save counts (8 / 4 / 0) -> distinct 12 / 1,467 / 4,136 and 4 / 2 / 0.
- C-03 RMSE 0.0227 (all steerer nodes) reproduces only with a default strength 0.05 for countries without `add`; with 0 it is 0.0291. Removed the hand-computed `alexandria` weight example (assumed BLG factor 2) earlier.

Could not be verified: the `k` of `add` (UNKNOWN as written), the "pull-direction model explained 77 to 198 of 602" statement (not re-run), Q6 and the outside-source points.
