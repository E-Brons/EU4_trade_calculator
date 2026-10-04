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
