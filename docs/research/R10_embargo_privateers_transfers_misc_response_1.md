# R10 response 1 - Embargo, privateers, node total vs sum(val) (data-based points only)

Scripts (`backend/scripts/research/`): `r10_gap.py`, `r10_gap_provinces.py`, `r10_pull_retain.py`, `r10_ppow.py`, `r10_stack.py`, `r01_embargo4.py`. Corpus: 82 saves, 6,560 node instances (6,525 with a node `total`).

## Q1/Q4 - What the gap `total - sum(val)` is (independent test, no circular subtraction)

### C-01 The gap is the trade power of provinces that no country entry receives
Claim: `node.p_pow` equals the sum of `trade_power` of all provinces of the node (provinces block, key `trade`); a country's `province_power` equals the sum of `trade_power` of the provinces whose **controller** is that tag. Provinces controlled by `REB` (rebels) or by nobody are credited to no entry; their power is inside `total` (valued with the `PIR` stub `max_demand = 1.0`) but in no entry's `val`.
Formula: `gap = total - sum(val) = sum(trade_power of provinces with controller in {REB, none})` (times PIR `max_demand` 1.0)
Source: save corpus, `r10_gap_provinces.py`, `r10_ppow.py`.
Quote (S01, gujarat): `p_pow 172.171`, sum of province `trade_power` by owner 172.171, listed `province_power` sum 171.575; the province `-514 Marwar owner=MER controller=REB trade_power=0.596`; MER's listed `province_power` 22.494 vs 23.09 for all its provinces there; gap 0.596.
Counts: `p_pow` minus the sum of listed `province_power` equals the gap in 273 of the 331 nodes with a gap > 0.0035: in 259 (78%) it is exactly the power of REB/uncontrolled provinces (tolerance 0.0035), in 14 more (S79/U02 lubeck; S80/U01 xian, the_moluccas, alexandria, ivory_coast, tunis, safi) it equals the uncredited province power but not the REB/uncontrolled sum; 58 nodes keep a gap that no province field explains (see C-02). (First version: "72 do not", which counted the 14 as unexplained; independent recomputation `ver_r10_gap.py`.) `node.p_pow` itself equals the sum of province `trade_power` only in 6,274 of 6,504 nodes with a `p_pow` (tolerance 0.002; 6,428 within 0.1; 21 nodes with a `total` have no `p_pow`); the deviations are mostly whole-number surpluses of 1-5 (S43 mexico 161.848 vs 160.848, S65 patagonia 27.836 vs 22.836). Province-level check (independent `ver_r10_provpow.py`, every entry except PIR): 3,420,278 of 3,420,670 (country,node) entries have `province_power` equal (0.002) to the sum of `trade_power` over provinces they control; 392 differ, 382 of them in S79/U02/S80/U01, 260 by more than 0.01, 90 by more than 0.1 and 58 by more than 0.5 (the first version's "356 of 3,403,570, mostly colonial nations with whole-number surplus" is replaced by this: colonial whole-number surpluses in the start saves are about 10 entries).
Confidence: confirmed for the 78% mechanism; the hypothesis "the gap is privateer power" is not supported for these nodes (rebels explain them without any pirate term).

### C-02 The residual (72 nodes) is UNKNOWN but has a structure
Claim: after removing REB/uncontrolled province power, 72 node instances keep a residual (66 positive, 6 negative; |residual| 0.021 to 9.707, median 3.379). The 6 negative and 8 more positive ones are the 14 nodes of C-01 whose gap equals `p_pow` minus credited province power exactly (played saves only); 58 positive residuals remain with no province-level explanation (S68 10, S70 10, S56 6, S57 6, S36 5, S80 4, U01 4, S53 3, S71-S74 2 each, S41 1, S64 1). Identical residual values repeat at several unrelated nodes of one save, which points to one country-level amount (not a node property): S36 5.771 at lahore, basra, samarkand and 5.022 at gujarat, gulf_of_aden; S53 5.263 at aleppo, alexandria, crimea; S56/S57 3.379 at ivory_coast, carribean_trade, st_lawrence and 2.423 at rheinland, bordeaux; S68 7.057 at ivory_coast, safi, carribean_trade and 5.144 at ethiopia, gulf_of_aden, aleppo; S79/U02 0.597 at lubeck.
Source: `r10_gap_provinces.py` ("residual grouped by (save, value)").
Confidence: inferred (structure only). Whether this amount is privateer power cannot be decided from the saved fields: no field of a pirate/privateer fleet is stored (the `PIR` entry holds only `max_demand` 1.0, and `potential` -0.001 in the 35 nodes without a `total`). What would settle it: a pair of saves that differ only in privateer fleets of one country.

## Q2 - `num_collectors_including_pirates`

### C-03 It is always num_collectors + 1, with no power attached
Claim: `num_collectors_including_pirates = num_collectors + 1` in every node where the pair exists, and `collector_power_including_pirates == collector_power` in every such node, so the extra collector is a phantom pirate collector with zero power, present whether or not the node has a gap.
Source: `r10_gap.py`.
Quote (corpus): node instances 6,560; `PIR` entry present in 6,560 (6,525 with only `max_demand`, 35 with `max_demand` and `potential`); `ncp - nc` = 1 in 5,906 nodes, keys absent in 654; `cpp - cp` = 0.0 in 5,906; `cpp != cp` in 0 nodes. The 35 nodes without node `total` are all `cape_of_good_hope` (one per save S01-S35... present in 35 saves).
Confidence: confirmed. So "+1 when privateer power > 0" is refuted (the +1 holds in nodes with gap 0 and with gap > 0 alike).

## Q3 - Pirates/uncredited power in retain_power and pull_power

### C-04 Neither contains a pirate or uncredited term
Claim: `retain_power` and `pull_power`, predicted from country entries only (project rules: retain = sum of effective power of collectors; pull = R03 rule), are exact in all nodes with a gap.
Source: `r10_pull_retain.py` (uses `calc.predict_stage`, tolerance 0.0035).
Quote: retain_power: gap nodes 331 ok / 0 fail; no-gap nodes 6,227 ok / 2 fail. pull_power: gap nodes 328 ok / 0 fail; no-gap nodes 5,487 ok / 4 fail. The failures are S79/U02 english_channel (retain 1858.846 vs 1860.64) and S79/U02 ohio, chesapeake_bay (pull), none of them gap nodes. Also `collector_power == retain_power` except 1 node.
Confidence: confirmed.
Updated 2026-10-05: one exception of the 'no uncredited term' statement: in U05 the stage checks of `pull_power` (`ethiopia`) and `retain_power` (`gulf_of_aden`) fail by exactly the `top_power` value of AFA, a country that lost its last province and has no entry there (section 'Update 2026-10-05', U-R10-1). The statement holds for every other node of U03, U04, U05.

## Q5 - Embargo: where it acts and how big

### C-05 The embargo acts on `max_demand` (hence `val`, retain/pull), and only where an embargoer has own power at the node
Claim: for embargoed countries (`trade_embargoed_by` non-empty), `max_demand` is below the country's class cap in nodes where an embargoer has own power (own = `max_pow - prev`: province + ship + flat merchant/capital extras, no propagated power); it equals the cap where none has.
Source: `r01_embargo4.py`, `r01_embargo2.py`; cap = the country's `max_demand` at same-class nodes (domestic/foreign) without embargoer own power; away rows multiplied by 2.
Quote (counts, 9,324 embargoed-country/node rows): no embargoer with own power -> not reduced 7,968, reduced 2; some embargoer with own power -> reduced 1,206, not reduced 148 (120 of the 148 have an embargoer share below 1% of the node's own power). "Reduced" = md more than 0.3% below the class cap (with an absolute 0.0015 threshold: 1,284 / 70; the 7,968 / 2 rows are unaffected). With the narrower measure province+ship only, 320 nodes were reduced although no embargoer had province/ship power (e.g. TUR aleppo, alexandria from HUN with own power 7.0 = a merchant's flat power), so the embargoer's merchant power counts, propagated power does not.
Confidence: confirmed for direction/presence; the money-only alternative is refuted for power: the reduction is inside `max_demand` and `val = max_pow * max_demand` holds; whether income is reduced additionally is UNKNOWN (income_efficiency stage is still open).

### C-06 The forum formula is approximately right but not exact
Claim: reduction ~= k * sum_e own_e / (sum own + 5*NH) with k about 0.57-0.60, not exactly 0.5.
Quote: single-embargoer rows: fitted k = 0.601, rmse 0.0269; grouped by (save, embargoer) the implied k has median spread 0.064 (NH coefficient a=2 gives the smallest spread, a=0 and a=5 are within 0.012: the `5*NH` term is not identified). S79 TUR rows (0.5*X predicted vs observed reduction, pp): malacca 3.44/3.79, basra 0.59/0.69, aleppo 1.35/1.37, alexandria 1.02/1.06, venice 2.69/2.90 reproduced within 1 pp; gulf_of_siam 10.59/13.27, canton 14.70/18.58, deccan 35.97/40.57, comorin_cape 24.08/27.49, gujarat 25.00/28.77, samarkand 18.17/21.75, persia 20.85/24.98, crimea 18.86/21.90, pest 27.76/31.18, wien 12.78/14.69, ragusa 17.66/19.68 not reproduced (observed 1.1-1.26 x predicted, per embargoer about BNG 1.25, DEC 1.14, RUS 1.16-1.20); astrakhan 50.00/47.96 (RUS only, share 1.0) the opposite direction.
Confidence: inferred. Per-embargoer `embargo_efficiency` and caravan power are not in the save, which would explain the per-embargoer factor; not proven.

## Q6 - TUR and several embargoers
TUR (S79) is embargoed by HUN, HAB, LUN, RUS, BNG, DEC. Only rows where an embargoer has own power are reduced (table in C-06); e.g. pest (HUN 44.6 + HAB 96.6) reduced 31.18%, ragusa (HUN 13.8 + HAB 89.8) 19.68%. Stacking: on 268 rows with >=2 embargoers the additive sum of shares fits slightly better than the product (rmse 0.0266 additive, k 0.583, vs 0.0288 multiplicative, k 0.632; k from single rows applied to multi rows: 0.0275 vs 0.0310). Reductions exceed 0.5 in 46 rows (max 0.815), so there is no cap of 50% in the data. Confidence: inferred (the difference is small).

## Not answered (needs an outside source)
- Q5 sources/quotes for `EMBARGO_BASE_EFFICIENCY`, `EMBARGO_MERCANTILISM_EFFICIENCY`, `embargo_efficiency`; Q7 (monopoly bonus, trade company region, blockade, treasure fleet effects) needs sourced statements; Q1 formula with `PIRATES_TRADE_POWER_FACTOR` needs the define.
- Q4 cause of the 72 residual nodes (C-02): UNKNOWN, needs privateer-fleet intervention saves.

## Verification (date 2026-10-04)
Independent recomputations: `ver_r10_gap.py`, `ver_r10_pirates.py`, `ver_r10_provpow.py` (plus `ver_r01_embargo.py` for C-05); re-runs of `r10_gap.py`, `r10_gap_provinces.py`, `r10_pull_retain.py`, `r10_stack.py`, `r01_embargo4.py`.
- Re-run and matching: 6,560 node instances, 6,525 with `total`, 35 without (all `cape_of_good_hope`); 331 gap nodes, 259 of them exactly REB/uncontrolled province power; the S01 gujarat worked example (p_pow 172.171, listed 171.575, MER 22.494 vs 23.09, province 514 Marwar 0.596, total 307.024 vs sum(val) 306.428); `num_collectors_including_pirates - num_collectors` = 1 in 5,906 nodes with the pair, `collector_power_including_pirates == collector_power` in all 5,906, PIR entry in 6,560 nodes (6,525 with only `max_demand`, 35 with `potential`); retain exact in 331 gap nodes and pull in 328 (failures only S79/U02 english_channel, ohio, chesapeake_bay); embargo presence 7,968 / 2; stacking (1,086 single / 268 multi embargoer rows; k 0.601 rmse 0.0269; multi additive 0.583 / 0.0266 vs multiplicative 0.632 / 0.0288; 46 rows above 0.5, max 0.815); the per-row S79 numbers of C-06.
- Corrected: "72 nodes not explained by provinces" -> 58 (14 of the 72 satisfy gap = `p_pow` - credited `province_power` exactly, all in S79/S80/U01/U02; all 6 negative residuals are among them); `node.p_pow` = sum of province `trade_power` is true for 6,274 of 6,504 nodes (not all), deviations mostly whole-number surpluses; province-level check 3,403,214 of 3,403,570 -> 3,420,278 of 3,420,670 with 392 mismatches, 382 of them in the four played-save files and only 58 above 0.5 (the "mostly colonial nations with whole-number surplus" description was wrong); "reduced" threshold of C-05 stated (0.3 % of the cap; 1,284 / 70 with an absolute 0.0015).
- Not verified: `r10_ppow.py` / `r10_max.py` outputs (the max-p_pow relation is not stated in this response); the 120-of-148 "share < 1 %" count was taken from the author's script output; "`collector_power == retain_power` except 1 node" was seen only in the author's printout; the S79 colonial-nation rows of the request_2 facts were not recomputed.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below are single runs of `backend/scripts/research/u345_pipe_*.py` (own code; `u345_pipe_stages.py` runs the project's `verify_world`); they have not been independently re-computed, unlike the Verification section above. New data: U03 (in-game date 1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 1691.11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign (player TUR, game 1.37.5, 80 trade nodes) as S79 (1665.4.22) and S80 (1682.4.18); they are not independent samples. Counts refer to these saves unless stated otherwise.

### U-R10-1 A vanished entry keeps its power in the node aggregates (U05)
In U05 (1693.4.15) the tag AFA, which lost its last province between U04 (1691.11.1) and U05, has no entry at `ethiopia` and `gulf_of_aden`, but:
- `pull_power` of ethiopia recorded 247.475 vs the project's calc 244.865: difference 2.610 = AFA's `top_power` value; `retain_power` of gulf_of_aden recorded 795.345 vs calc 787.827: difference 7.518 = AFA's `top_power` value there. These are the only two failures of these stages in U05.
- `max` of both nodes exceeds `p_pow` + the sum over present entries by exactly 2.0 and 7.0; the link `ethiopia -> gulf_of_aden` keeps `incoming.add` 0.377 = 5.804 x 1.0 x 0.065 (AFA's `add` in U03/U04).
So retain and pull can contain power that no current entry carries. This is a different cause from rebel-held provinces (C-01) and from privateers: a country without entry, one monthly computation old (confirmed as a description of this save; that the aggregates are the last tick's is inferred from one event). In nodes without such a country `retain_power` and `pull_power` follow the entries exactly (C-04).

### U-R10-2 Stage results on the new saves
`retain_power` 0/80 (U03), 0/80 (U04), 1/80 (U05); `pull_power` 0/77, 0/77, 1/77 (the U05 failures are the AFA case). The gap `total - sum(val)` and the 58 unexplained residual nodes (C-02) were not analysed in U03-U05: UNKNOWN there. Embargo (C-05, C-06): not re-tested here (U03-U05 were examined for the away factor and home bonus only).

### Verification 2026-10-05 (second pass)

Method: new code `backend/scripts/research/ver2_c_stages.py` (project `verify_world` over all 85 manifest saves; U01/U02 are copies of S80/S79, so corpus-wide counts contain two duplicates), `ver2_c_identities.py` (own re-computation of the identities, prev rule, gate and ship-term counts from the parsed trade trees, exact decimal truncation), `ver2_c_gates.py`, `ver2_c_worst.py`.

Matched: `retain_power` 0/80, 0/80, 1/80 and `pull_power` 0/77, 0/77, 1/77 in U03/U04/U05, the two U05 failures are the only ones in that save; the differences 2.610 (`ethiopia`) and 7.518 (`gulf_of_aden`) equal AFA's `top_power` values; `max` exceeds `p_pow` + entries by exactly 2.0 and 7.0; `incoming.add` 0.377 = 5.804 x 1.0 x 0.065. Over all 85 saves `retain_power` has 1 failure in 6,800 checks and `pull_power` 5 in 6,050 (3 distinct nodes). AFA in the countries block: U03 and U04 `owned_provinces [2764]`, `num_of_cities 1`, `development 5.0`; U05 no `owned_provinces`, `num_of_cities` or `development` (119 keys against 146) and no entry of any kind in the 80 trade nodes (U04: 80 entries).
Refinement: the AFA numbers in the aggregates are not "AFA's old power" as in U04: at `ethiopia` max_pow 2.0 x max_demand 1.305 = 2.61 and at `gulf_of_aden` 7.0 x 1.074 = 7.518, where 7.0 = U04's 13.26 without province power (1.26) and without the 5.0 of `merchants_too_succesful` (24 days left in U04), and 1.305 / 1.074 are 0.012 above AFA's U04 max_demand (1.293 / 1.062; not readable in U05). So the aggregates were computed after the province was lost (inferred, one event).
Unverifiable: `total - sum(val)` and the residual nodes in U03-U05 were not analysed; embargo and privateers not re-tested.
