# R09 response 1 - Save field dictionary (data-derived points only)

Scope: this response answers only the points of `R09_save_field_dictionary_request_1.md` that the 82 fixture saves can settle (S01-S80 plus U01/U02). Every claim below is derived from the saves by a script (`backend/scripts/research/r09_r13_*.py`, listed per claim) and rests on verbatim save rows, not on an outside source. `confirmed` is used only where the whole corpus was tested with counts and the exceptions are listed; everything else is `inferred`. Points that need an outside source are listed at the end under "Not answered".

Corpus facts used throughout: 82 saves, 6,560 node blocks, 3,427,230 country-in-node entries (`TAG={...}` inside a node; 3,316,641 of them carry only `max_demand`). **U02 is the same date as S79 and U01 the same date as S80 and gives identical numbers in every test below, so the played saves are two distinct saves counted twice each.** "Played saves" = S79, S80, U01, U02 (not saved on the 1st; see R12).

---

## Q1 - Fields whose dictionary cell contradicts verified results

### C-01 `power_fraction`
Claim: `power_fraction = trunc3(effective / retain_power)` with `effective = val - t_out + t_in`, present exactly for the collecting entries.
Formula: `power_fraction = trunc3((val - t_out + t_in) / node.retain_power)`; `trunc3(x) = floor(x*1000)/1000`.
Applies when: the entry has the key `total` (collecting). In every node the set of entries with `power_fraction` equals the set with `total` equals the set with `money` (6,560 of 6,560 nodes).
Source: save corpus, `r09_r13_q1.py`.
Quote: S14 `alexandria` HED `power_fraction=0.175`: `trunc3(28.062/159.516)=0.175`; MAK `0.045`: `trunc3(7.224/159.516)=0.045`; MDA `0.055`: `trunc3(8.828/159.516)=0.055`.
Confidence: confirmed (42,948 entries; 7 failures, all in S64 `genua`: SPI stored 0.124, GEN 0.271, KNI 0.022 against retain_power 326.299; the same node whose `retain_power` the project already lists as failing).
Caveats: `val / node.total` (the draft's cell) is not the definition: for MAM in the same node `115.402/275.499 = 0.419`, stored `power_fraction = 0.723 = 115.402/159.516`.

### C-02 `potential`
Claim: for entries with transfers, `potential = trunc3((t_out - t_in) / node.total)`; positive for givers, negative for receivers.
Formula: as stated.
Applies when: the entry has `t_in` or `t_out`.
Source: save corpus, `r09_r13_q1.py`.
Quote: see R04 request Q5 for rows; the corpus run gives 3,584 entries with `t_in`/`t_out`, 3,584 reproduced, 0 failures.
Confidence: confirmed for entries with transfers. Note `trunc3`, not rounding, and truncation toward zero: for the negative values of receivers `floor` is wrong (independent recount: 2,232 entries fit `floor(x*1000)/1000`, the other 1,352, all negative, fit truncation toward zero).
Caveats / new finding: `potential` also exists on **23,660 entries without any transfer**, all in the node `cape_of_good_hope` of 35 saves (the node has no power at all: it has no `total`, no `p_pow`, `retention=1.0`). There every entry (stub with only `max_demand`) carries `potential=-0.002` (23,625 entries) and `PIR` carries `-0.001` (35 entries). The formula is undefined there (no node total). Rule: UNKNOWN. Other nodes carry no `potential` on entries without transfers.

### C-03 `pull_power`
Claim: `pull_power = sum of effective power of the countries that steer in the node, plus those that do not collect in it but collect in some node downstream (any number of hops)` (the integrated R03 rule).
Formula: pulling(tag, node) = (has_trader and `type` key present) or (no `total` key here and the tag has `total` in a node reachable downstream); `pull_power = sum over pulling tags (val - t_out + t_in)`.
Source: save corpus + `tradenodes.json` graph, `r09_r13_q1.py`. Own re-implementation (not `calc.py`) over all saves.
Quote: failures: S79 and U02 `ohio` (rule 402.981, stored 440.306) and `chesapeake_bay` (607.474 vs 646.532).
Confidence: confirmed on 5,815 of 5,819 nodes with `pull_power` (4 failures, 2 nodes in the one played save, the known POR-receiver case of R04 Q6). The draft's wording ("trade power of non-collecting countries steering forward") is incomplete: it omits the non-steering pullers.

### C-04 `max_demand`
Claim (data only, no formula): `max_demand` exists for every country at every node (3,426,880 of 3,427,230 entries; the 350 without it are the `potential`-only stubs of C-02), ranges from 0.281 to 2.793, is below 1.0 in 308,713 entries, above 2.0 in 2,436, exactly 1.0 in only 6,640 (0.19%), and `val = trunc3(max_pow * max_demand)` holds in 85,892 of 85,892 entries with the three fields.
Source: save corpus, `r09_r13_q1.py`.
Confidence: confirmed as a description of the data; the definition (which modifiers it contains) is UNKNOWN from the saves. The draft's `1.0 + global_trade_power_modifiers` is contradicted: 308,713 entries are below 1.0 and the value varies by node for one country. Whether the away penalty, embargo or home bonus are inside it is the subject of R01/R02 and cannot be settled by this task.

### C-05 `num_collectors_including_pirates`
Claim: in every one of the 5,906 nodes that have `num_collectors`, `num_collectors_including_pirates = num_collectors + 1`, a `PIR` entry exists in the node (it holds only `max_demand=1.0`), and `collector_power_including_pirates == collector_power` (5,906 of 5,906, to 0.0015).
Source: save corpus, `r09_r13_q1.py`, `r09_r13_nodefields.py`.
Quote: S14 `alexandria`: `num_collectors=4`, `num_collectors_including_pirates=5`, `collector_power=159.516`, `collector_power_including_pirates=159.516`, entry `PIR={ max_demand=1.0 }`.
Confidence: confirmed as a description. The "+1" is a constant, so it is the pirate entry counted as a collector with zero power; its meaning in the game is UNKNOWN from the saves (and the draft's "nations + pirate privateers" is not testable). Also `num_collectors` = number of entries with a `total` key in 5,899 of 5,906 nodes; the 7 exceptions: S64 `genua` (8 vs 7 entries), S79/U02 `california` (9 vs 8), S79/U02 `english_channel` (9 vs 8), S80/U01 `gulf_of_siam` (2 vs 1).

---

## Q2 - Fields guessed without evidence

### C-06 `p_pow`
Claim: `p_pow` = the sum of the stored `trade_power` of all provinces whose `trade=<node>`, attributed by controller, **including provinces held by rebels (controller `REB`)**; it is therefore larger than the sum of the entries' `province_power` in exactly the nodes where rebels hold provinces.
Formula: `p_pow = sum over provinces with trade==node of province.trade_power`.
Source: save corpus (`provinces` blocks), `r09_r13_provpow4.py`, `r09_r13_nodefields.py`.
Quote: S01 `gujarat`: `p_pow=172.171`, sum of entries' `province_power` = 171.575, difference 0.596 = province `-514` (Marwar) `owner=MER controller=REB trade_power=0.596`. S01 `ethiopia`: 73.006 - 72.618 = 0.388; `gulf_of_aden`: 143.248 - 142.654 = 0.594.
Confidence: confirmed that the 283 nodes where `p_pow` exceeds the entries' `province_power` are exactly the 283 nodes with rebel-held provinces (283 = 283 = 283 intersection); the equality `p_pow = sum(province trade_power)` holds in 6,350 of 6,504 nodes (independent recount, tolerance 0.0005 per summed province plus 0.0005; 26 of the 283 rebel nodes are among the failures). The 154 failures: 142 are in the played saves (stale between ticks, inferred), 12 are in start saves with a whole-number difference (+1.0 in S43 `mexico`, S56/S59/S60 `patagonia`, S68/S70 `sevilla`; +5/+3 in S65/S66 `patagonia`/`laplata`; +2/+5 in S72 `amazonas_node`/`carribean_trade`): a flat integer that is in no province's `trade_power`; its cause is UNKNOWN. (The first version of this text said 6,344 / 160 / 148; the 6 extra nodes are borderline played-save nodes that depend on the display-rounding tolerance.)

### C-07 `max`
Claim: `max = p_pow + sum over entries of (max_pow - prev - province_power)`, i.e. the node's provincial power (`p_pow`, rebels included) plus the entries' ship power and flat extras. (Corrected: the first version wrote `p_pow + sum(max_pow - prev)`, which counts the provincial power twice; `max = sum(max_pow - prev)` alone fits only the 6,220 nodes without rebel-held power.)
Formula: `max = p_pow + sum(max_pow - prev - province_power) = p_pow + sum(ship_power + extras)`.
Source: save corpus, `r09_r13_nodefields.py`.
Quote: S01 `kongo`: `p_pow=73.29`, `max=128.29`, difference 55.0 = 11 capital entries each with `max_pow - province_power - prev - ship_power = 5.0` (KON, TYO, KSJ, LUB, LND, CKW, KIK, KZB, YAK, KLD, KUB). S14 `alexandria`: `p_pow=136.077`, `max=156.077`, `sum(max_pow - prev)=156.077`.
Confidence: confirmed for 6,503 of 6,504 nodes (6,345 without ship power; 158 with ship power, where the ships are part of the sum). The single failure is S64 `genua` (difference 40.0 vs 35.0 explained by entries).
Updated 2026-10-05: on the new saves the identity holds in 80/80 nodes (U03, U04) and 78/80 (U05); the two U05 exceptions are `ethiopia` and `gulf_of_aden`, where `max` exceeds `p_pow` + the present entries by exactly 2.0 and 7.0 because a country that lost its last province (AFA) left its old power in the node (section 'Update 2026-10-05', U-R09-2).
Caveats: the "oddity" `max - p_pow = 25.000` of the goal is the sum of five flat extras of 5.0 (a node with five capital entries); I do not claim the goal's two example nodes are the same node.

### C-08 `highest_power`
Claim: `highest_power` = the trade power of the single strongest **province** in the node (not of a country).
Source: save corpus, `r09_r13_provpow4.py`.
Quote: S01 `kongo`: `highest_power=15.6` while the largest country `province_power` is 19.77 (KON), i.e. the cell cannot be a country sum; equals the largest `trade_power` of one province with `trade=kongo`.
Confidence: confirmed in 6,480 of 6,504 nodes; the 24 failures are all in the played saves. This explains the goal's oddity `highest_power 17.371` against `top_power_values` starting at 44.434 (a province against a country).

### C-09 `collector_power`
Claim: `collector_power = retain_power` (5,905 of 5,906 nodes; failure S64 `genua`); `collector_power_including_pirates` is identical (5,906 of 5,906).
Source: save corpus, `r09_r13_nodefields.py`. Confidence: confirmed. It is a duplicate field, not new information.

### C-10 node `total`
Claim: `total = sum of val of all listed entries` plus the power of rebel-held provinces.
Quote: S01 `gujarat`: `total=307.024`, sum of entry `val` = 306.428, difference 0.596 (the rebel province of C-06).
Confidence: confirmed that 259 of the 331 nodes where `total` exceeds `sum(val)` by more than 0.01 equal the rebel-held province power; the other 72 (for example S36 `lahore` 5.771, `gujarat` 5.022, `gulf_of_aden` 5.022, `samarkand` 5.771; S41 `crimea` 2.763; S53 `alexandria` 5.263; `basra` 11.686 vs rebel 5.915) are not explained by rebels. They belong to R10 (pirates); no independent test is possible here.

### C-11 `top_power`, `top_power_values`
Claim: `top_power` lists every tag whose **effective** power `val - t_out + t_in` is above 0, sorted descending, and `top_power_values` are those effective powers (not `val`, not `max_pow`, not `province_power`).
Source: save corpus, `r09_r13_toplists.py`.
Quote: S36 `amazonas_node` CAS: `top_power_values=8.667` = `val 3.31 + t_in 5.357`; C01: `5.458 = val 10.815 - t_out 5.357`.
Confidence: confirmed: 6,525 of 6,525 nodes (all values to 0.0015; the set of tags equals the set with effective power above 0; maximum list length 38).

### C-12 `top_provinces`, `top_provinces_values`
Claim: lists every tag with `province_power > 0`, sorted descending, values = the entry's `province_power`. A node whose tags all have 0 province power omits both keys (21 nodes).
Source: save corpus, `r09_r13_toplists.py`. Confidence: confirmed (6,504 nodes carry the keys and all 6,504 fit; the other 21 of the 6,525 nodes with `top_power` have no province power at all; maximum length 37).

### C-13 `already_sent`
Claim: `already_sent = province_power / 5 * k` with a whole number `k` in 1..5.
Source: save corpus + graph, `r09_r13_alreadysent.py`.
Quote: S14 `kongo` KON `already_sent=3.954`, `province_power=19.77` (k=1); `zambezi` ZIM `5.808` vs `29.04` (k=1); `california` CNK `6.82` vs `17.05` (k=2).
Confidence: inferred. k is a whole number in 17,108 of 17,114 entries with the field (histogram: k=2: 5,749; 1: 5,269; 3: 3,286; 4: 1,814; 5: 990; 6 entries 1.04/1.11/4.2). `k` equals the number of upstream nodes of the node in the trade graph in 15,316 of 17,114 entries (89.5%); S01 `mexico` is an exception (in-degree 2, k=1). It looks like the power the country has already sent upstream from this node (the same `/5` as `prev`, see C-14), but this is a reading: the rule that decides k is UNKNOWN. The field is absent on 36,828 entries with `province_power > 0` (1,228 of them with `province_power >= 10`). It does not equal `val`, `t_out`, `prev`, `max_pow`, `money`, `outgoing`, `current` or `total` (0 matches in 17,114 for each of `val`, `eff`, `node.total`, `node.current`; 186 for `max_pow`, 522 for `province_power`).

### C-14 `trade_goods_size`, `local_value`
Claim: `trade_goods_size` is a 33-entry list of goods produced per goods type in the node, in the order of the keys of the top-level `change_price` block of the same save: `nogoods, grain, wine, wool, cloth, fish, fur, salt, naval_supplies, copper, gold, iron, slaves, ivory, tea, chinaware, spices, coffee, cotton, sugar, tobacco, cocoa, silk, dyes, tropical_wood, livestock, incense, glass, paper, gems, coal, cloves, unknown`. Index 0, 30 (coal) and 32 are 0 in every node of S01. Each size is about `0.2 * sum(base_production of the provinces producing that good)` in the 1444 saves (independent recount: median ratio to `0.2 * base_production` is 1.00 for 29 of 30 goods in S01, S14 and S36; cloves 1.1, i.e. 0.22, so a modifier exists, UNKNOWN). In the later saves S42 and S60 most goods have a median ratio of 1.02-1.2, so the plain 0.2 rule does not hold there (another modifier, UNKNOWN). `local_value = sum(size_i * current_price_i) / 12`. Details and validation: see R13 response, C-01.
Source: save corpus, `r09_r13_goods.py`, `r09_r13_prices.py`.
Confidence: confirmed for the index order (read from the save); inferred for the size rule.

### C-15 `most_recent_treasure_ship_passage`
Claim: the value is `1.1.1` in all 6,560 node blocks of all 82 saves (including the played saves), so it carries no information in this corpus. Confidence: confirmed (data fact). Meaning: UNKNOWN.

### Not settled
`max` in the sense of "a maximum of what" beyond C-07: settled. `total` of an entry (`TAG.total`): see R07/R10. `potential` formula for non-transfer nodes: UNKNOWN (C-02).

---

## Q3 - `prev` and `max_pow`

### C-16 `prev`
Claim: for a country, `prev` at node N = sum over the **directly downstream** nodes D of N (the outgoing links of N in the graph) of `province_power(country, D) / 5`, counting a node D only if the country's `province_power` in D is at least 10; owner of the power: the same country.
Formula: `prev(c, N) = trunc3( sum over D in outgoing(N) of [province_power(c,D)/5 if province_power(c,D) >= 10 else 0] )`.
Applies when: the entry exists (entries with `max_pow` or `prev`).
Source: save corpus + graph, `r09_r13_prev.py`.
Quote: S80 `kongo` MOR: downstream province powers `[51.36, 0.0]`, rule 10.272, stored `prev=10.797`. S01 `california` XAL: downstream `[11.31, 0, 0, 0]`, rule 2.262, stored 0.
Confidence: confirmed on 85,968 entries: the thresholded one-hop rule fails 73 times (99.915%); the plain `sum/5` (no threshold) fails 5,271 times; `>10` and `>=10` give the same 73 (an exact 10.00 case does not exist). The 73 failures: `california`/XAL (40 entries across saves, downstream 11.31 but `prev=0`), `patagonia`/INC (5), `cuiaba`/C04 (5), `gujarat`/POR (5), `tunis`/SPA (5), `amazonas_node`/C03 (3), and MOR in S80/U01 (`kongo`, `katsina`, `cape_of_good_hope`, `brazil`, `timbuktu`, 2 each, stored `prev` larger than the rule by 0.525, 0.525, 0.525, 0.525 and 0.875).
Updated 2026-10-05: in played saves the failures of the ungated rule are a few `polynesia_node` entries and the MOR ship cases; U04 (a tick day) fails like the mid-month saves (section 'Update 2026-10-05', U-R09-3 and the R05 update).
Caveats: truncating each link's `province_power/5` before adding (R05 response) gives 63 failures instead of 73 on the same 85,968 entries, so the per-link form is the closer one. This test counts entries that have `max_pow` or `prev`; R05's own count (108,562 entries) includes entries without those keys and finds 163 failures; the two bases differ and neither is wrong.

### C-17 `max_pow` components
Claim: `max_pow = province_power + ship_power + prev + extras`, where `extras` is a flat residual that takes few values.
Source: save corpus, `r09_r13_examples.py`.
Quote (value counts of `max_pow - province_power - ship_power - prev` over 85,968 entries): 5.0 -> 42,310; 0.0 -> 41,205; 2.0 -> 986; 7.0 -> 442; 17.0 -> 436; 22.0 -> 248; 20.0 -> 115; -8.0 -> 72; -3.0 -> 68; 12.0 -> 42; 27.0 -> 24; -10.0 -> 12; 42.0 -> 4; -5.0 -> 4.
Confidence: confirmed as a description of the data (the "extras" are a residual, not a model; their decomposition is R06). 2,453 entries are outside {0, 5}.

---

## Q4 - Country-level fields (what they contain, which feed the calculation)

All from `countries={TAG={...}}`, `r09_r13_country.py`, `r09_r13_country2.py`, `r09_r13_homebonus.py`. Instances = country-save pairs that carry the key.

| field | content | evidence (corpus) | feeds the trade calculation? |
|---|---|---|---|
| `trade_port` | province id | equals the country's `capital` in 42,754 of 42,754 country-saves that have a `has_capital` entry; the node of that province is the node whose entry has `has_capital` in 42,754 of 42,754 | yes (the `has_capital` input). The corpus never has `trade_port != capital`, so it cannot say which of the two defines `has_capital` |
| `merchants={envoy={...}}` | list of `{id, name, type, action?}` | `type=1` in all 107,275 envoys; `action=2` in 63,648, absent in 43,619, `action=1` in 8. Number of `action=2` envoys = number of nodes where the country has `has_trader` in 42,588 of 42,754 (99.6%); number of envoys >= that number in 42,754 of 42,754 | state: `action=2` = placed in a node (inferred), absent = not placed. Meaning of `action=1` (8 cases) and of `type`: UNKNOWN |
| `trade_embargoes`, `trade_embargoed_by`, `num_of_trade_embargos` | tag lists / count | exist only in S79, S80, U01, U02 (126 / 118 / 126 country-saves). Reciprocal: B in A.`trade_embargoed_by` iff A in B.`trade_embargoes` in 236 of 236 cases in both directions; `num_of_trade_embargos = len(trade_embargoes)` in 126 of 126 | state, input of the multiplier (R01/R10) |
| `transfer_trade_power_from`, `_to` | tag lists | 154 / 492 country-saves in 47 saves; they equal the tags found in the entries' `t_from` / `t_to` in 152 of 154 and 490 of 492. Exceptions: S80/U01 TUR lists `BEI` (and BEI lists TUR) while no node entry shows a `t_from`/`t_to` for BEI | state; the lists can name a partner that contributes nothing at the moment |
| `num_ships_protecting_trade` | integer | only in the played saves (290 country-saves); equals the sum of `light_ship` over the country's entries in 278 of 290 (12 failures: S79/U02 5 each, S80/U01 1 each, e.g. S79 DAN 41 vs 39, GBR 40 vs 35, SPA 70 vs 53) | describes state; the node entries are the input |
| `trade_mission` | float 0.013..2.0 | only in the played saves (418 country-saves) | meaning UNKNOWN |
| `traded` | 33 numbers, goods order of `change_price` | present for all 113,160 country-saves; the sum is not `money` (136 of 42,754 equal), `val`, the `total` shares or the node `current` of the collecting nodes (22 of 42,754) | meaning UNKNOWN; describes state |
| `traded_bonus` | list of goods indices | 405 country-saves in all 82 saves, e.g. S01 MAJ `[31]` (cloves), S80 TUR `[16, 18, 26, 27, 31]` (spices, cotton, incense, glass, cloves) | meaning UNKNOWN |
| `mercantilism` | float | 2.0..48.0, all 113,160 country-saves | modifier source, not stored as a trade variable |
| `transfer_home_bonus` | float, multiples of 0.1, 0.0..0.9 | zero in all 78 start saves for every country; non-zero only in S79/S80/U01/U02: 1,792 country-saves (S79 444, S80 452, U01 452, U02 444), of which 362 belong to countries that have a `has_capital` entry (the only ones that can be tested). In all 362 the country has at least one merchant steering into its home node and no merchant collecting away; but `0.1 x number of home-steering merchants` reproduces only 102 of the 362 values. 11,266 country-saves with home-steering merchants have 0.0, but 11,144 of them are start saves where the field is always 0; in the played saves 122 such countries have 0.0 against 362 with a non-zero value. | the rule is UNKNOWN; it is a candidate for the "home bonus" of R01/R02 and for the R12 question (it is 0 in every snapshot that was not ticked) |

Confidence for every row: confirmed as a description; meanings marked UNKNOWN stay UNKNOWN. No field is a stored `trade_efficiency` or `global_trade_power` (consistent with the goal).

---

## Q5 - Real validation (one node, S14 `alexandria`, arithmetic)

All rows are taken from the save `S14_TUR_1444.11.11.eu4`, node `alexandria`, script `r09_r13_examples.py`.

| check | arithmetic | stored | result |
|---|---|---|---|
| `total = sum(val)` | sum of all entry `val` = 275.499 | `total=275.499` | reproduced |
| `retain_power = sum(val - t_out + t_in)` of collectors | HED 28.062 + MAK 7.224 + MDA 8.828 + MAM 115.402 = 159.516 | `retain_power=159.516` | reproduced |
| `collector_power = retain_power` | 159.516 | `collector_power=159.516` | reproduced |
| `val = trunc3(max_pow * max_demand)` | HED `trunc3(28.26*0.993)=28.062`; MAK `trunc3(7.16*1.009)=7.224`; MDA `trunc3(8.75*1.009)=8.828`; MAM `trunc3(110.539*1.044)=115.402` | the same four | reproduced |
| `power_fraction` | HED `trunc3(28.062/159.516)=0.175`; MAK `0.045`; MDA `0.055`; MAM `0.723` | same | reproduced |
| `total` (entry) `= trunc3(current * power_fraction)` | HED `trunc3(5.052*0.175)=0.884`; MAK `0.227`; MDA `0.277`; MAM `3.652` | same | reproduced |
| `max = p_pow + sum(max_pow - prev)` | 136.077 + 20.0 (4 capitals x 5.0) = 156.077 | `max=156.077` | reproduced |
| `p_pow = sum(entries' province_power)` | 136.077 (no rebel-held province here) | `p_pow=136.077` | reproduced |
| `top_power_values` | MAM 115.402, HED 28.062, TUR 21.409, VEN 18.711 (= effective power) | same | reproduced |
| `top_provinces_values` | MAM 105.539, HED 23.26, MDA 3.75 | same | reproduced |
| `retention = retain/(retain+pull)` | 159.516/(159.516+101.429) = 0.6113 | `retention=0.612` | **fails by 0.0007**: the stored value is not the truncation or rounding of the quotient. `current = (6.433 + 0.421+0.618+0.782) * retention`: with the stored 0.612 it is 8.254*0.612 = 5.0514 (stored `current=5.052`); with 0.6113 it would be 5.0457. This is the known open point of the README log (`retention` is not a plain quotient); no cause can be derived from this node |

The goal's own example values (`retain_power 58.273 + pull_power 126.61 = 184.883 = total`, `retention 0.316`) cannot be assigned to a node from the goal; I did not try to match them.

---

## Not answered (needs an outside source)

- Q1: a sourced/quoted definition of `max_demand` and a sourced meaning for pirates (`num_collectors_including_pirates`).
- Q2: a game-file or schema source for `local_value`, `trade_goods_size` and the modifier behind cloves 0.22 and the 2-20% deviations in the later saves.
- Q3: a source for `prev` (the 5% / 73 entries have no mechanism here) and for the content of `max_pow` beyond the residual.
- Q4: pdx-tools / eu4save / rakaly schema files and paths for every field; units of `traded`, `traded_bonus`, `trade_mission`; what `type` and `action` of an envoy mean.
- Q6: all of it (URLs, file paths, version banners; whether C-01 to C-03 of the draft can be sourced).

---

## Verification (date 2026-10-04)

Independent recomputation (new code, not the author's logic): `backend/scripts/research/ver_r09_nodes.py`, `ver_r09_nodes2.py`, `ver_r09_countries.py`, `ver_r09_homebonus.py`, `ver_r09_misc.py`, `ver_r13_prov.py`, `ver_r13_quotes.py`, `ver_r13_localvalue.py`, `ver_r13_goods.py`. Graph for `prev`/`pull_power` built from the saves' own `incoming.from`; province sums from the `provinces` blocks of all 82 saves.

**Matched (claim and numbers reproduced):** corpus counts (6,560 nodes, 3,427,230 entries, 3,316,641 max_demand-only); C-01 (42,948 entries, 7 failures all S64 `genua`; equal key sets in 6,560 of 6,560 nodes); C-02 (3,584 of 3,584); C-03 (5,815 of 5,819; the 4 failures are S79/U02 `ohio` and `chesapeake_bay` with the quoted values); C-04 (all counts, 0.281..2.793, 308,713 / 2,436 / 6,640, 85,892 of 85,892, 350 potential-only stubs); C-05 (5,906 of 5,906; the 7 `num_collectors` exceptions); C-06 (283 = 283 = 283, 26 rebel nodes among the failures, S01 `gujarat`/`ethiopia`/`gulf_of_aden` differences, `-514 Marwar`); C-07 (6,503 of 6,504, 6,345 / 158, the S64 `genua` failure, the `kongo` 11 capital entries); C-08 (6,480 of 6,504, the 24 failures all in played saves); C-09; C-10 (331 gap nodes, 259 = rebel power, the 72 named residual examples); C-11 (6,525 of 6,525, max length 38); C-12 (6,504 nodes, 21 without province power, max length 37); C-13 histogram and the 36,828 / 1,228 absent counts and the 15,316 in-degree matches; C-14 index order (identical in all 82 saves) and the zero indices 0, 30, 32 in S01; C-15 (6,560 of 6,560); C-16 (73 failures, the 73 by node/tag, plain `sum/5` 5,271, `>` and `>=` identical, MOR residuals 0.525 x4 and 0.875); C-17 (all value counts, 2,453 outside {0, 5}); Q4 table (113,160 country-saves, envoy counts, 236 of 236 reciprocal embargoes, 126 / 118 / 126 key counts, 154 / 492 transfer lists with 152 / 490 matches and the BEI exception, 290 and 278 with the 12 `num_ships_protecting_trade` failures, 418 `trade_mission`, 405 `traded_bonus`, mercantilism 2.0..48.0, 42,754 `trade_port` = `capital` = has_capital node); Q5 (every row of the S14 `alexandria` table, including the `retention` failure 0.6113 vs 0.612 and 5.0514 vs 5.0457).

**Corrected (old -> new, why):**
- C-07 formula: `max = p_pow + sum(max_pow - prev)` -> `max = p_pow + sum(max_pow - prev - province_power)`. The old form double counts the provincial power (it fits 0 of 6,504 nodes); the corrected form fits the stated 6,503 of 6,504 (`sum(max_pow - prev)` alone fits only the 6,220 nodes without rebel-held power). The counts in the text were already those of the corrected form.
- C-06: 6,344 of 6,504 (160 failures: 148 played, 12 start) -> 6,350 (154: 142 played, 12 start); the 6 nodes are borderline played-save nodes that depend on the rounding tolerance. S72 start-save surpluses completed (+2 `amazonas_node`, +5 `carribean_trade`).
- C-12: "6,525 of 6,525 nodes" -> 6,504 nodes carry the keys and all fit; the other 21 nodes have no province power.
- C-13: k whole in 17,098 -> 17,108 of 17,114 (the response's own histogram sums to 17,108).
- C-14: "median ratio 0.200 for 29 goods in a 5-save sample" -> true for S01, S14, S36 only (cloves 1.1); in S42 and S60 most goods are 1.02-1.2, so the 0.2 rule does not hold in later saves. The "cocoa 0.2012" remark was not reproduced and was removed.
- C-02: truncation is toward zero (floor fails on the 1,352 negative receiver values).
- Q4 `transfer_home_bonus`: "362 country-saves, zero in all 82 start saves" -> 1,792 non-zero country-saves in the four played-save files, of which 362 have a `has_capital` entry and can be tested; the 102 of 362 and the "home-steering merchants and none collecting away in 362 of 362" are reproduced; the 11,266 zero cases are 11,144 start-save cases plus 122 in the played saves; start saves are 78, not 82.
- C-16 caveat added: truncating each link before adding gives 63 failures instead of 73.

**Could not be verified / not re-tested:** `S01 kongo` and the other quoted node rows beyond those listed above were checked only where named; the exact tolerance behind the author's 73 (tolerance 0.0015 reproduces it); the Q4 claim that `action=2` means "placed in a node" (inferred, only correlational: 42,588 of 42,754); `traded` sum comparisons (136 / 22 of 42,754) and the 11,266 figure are taken from the author's run of `r09_r13_homebonus.py` (re-run, same output) rather than recomputed independently; the `comorin`-type ratios of Q1 sources are not applicable (all outside-source points remain unanswered by design).

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below are single runs of `backend/scripts/research/u345_pipe_*.py` (own code; `u345_pipe_stages.py` runs the project's `verify_world`); they have not been independently re-computed, unlike the Verification section above. New data: U03 (in-game date 1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 1691.11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign (player TUR, game 1.37.5, 80 trade nodes) as S79 (1665.4.22) and S80 (1682.4.18); they are not independent samples. Counts refer to these saves unless stated otherwise.

### U-R09-1 Identities re-run on the new saves (U03 / U04 / U05)
- `val == trunc3(max_pow x max_demand)`: 866/866, 869/869, 859/859 (stage `val`, 0 failures).
- `top_power_values` equals `val - t_out + t_in` for the pairs that have an entry: 866/866, 869/869, 859/859 (see U-R09-2 for the entry-less tag in U05).
- `max = p_pow + sum(max_pow - prev - province_power)` within 0.0035: 80/80 (U03), 80/80 (U04), 78/80 (U05; `ethiopia`, `gulf_of_aden`).
- `potential` and `t_in`/`t_out` (stage `transfers`): 0 failures in 436, 436, 432 checks. Stage `income_share`: 0 failures in 368, 368, 362 checks. `retention`: 0 failures in 80 nodes each.
- `pull_power` and `retain_power`: 0/77 and 0/80 (U03, U04), 1/77 and 1/80 (U05, the stale case below).
- `value_added_outgoing == outgoing`: 77/77 nodes with links each (R08 C-07); link identities 159/159 links each (one `incoming.add` exception in U05).

### U-R09-2 Node fields that keep the power of a country without an entry (new)
In U05 the tag AFA (last province lost between U04 and U05) has no entry at `ethiopia` and `gulf_of_aden`, but these node fields still contain its old values: `top_power` lists it (2.61 and 7.518), `pull_power` of ethiopia exceeds the calculation by 2.610 and `retain_power` of gulf_of_aden by 7.518, `max` exceeds `p_pow` + the present entries by 2.0 and 7.0, and the link `ethiopia -> gulf_of_aden` keeps `incoming.add` 0.377 (AFA's old `add` 0.065 x 5.804). So the C-11 statement "`top_power_values` are the entries' effective powers" has an exception when a country has just lost all provinces: the node lists are then one monthly computation older than the entries (confirmed as a description of U05; the reading "the lists keep the last monthly tick" is inferred from one event; see the R12 update).

### U-R09-3 `prev` (C-16)
The ungated one-hop rule with per-link truncation and threshold 10 is exact in 959/963 (U03), 963/967 (U04), 951/955 (U05) candidates; the 4 misses per save are `polynesia_node` entries (C02, C03, C12, HOL) with recorded `prev` 0 (R05 update). `max_pow` extras: not re-decomposed in the new saves (the stage `raw_power` fails in 527/883, 528/886, 519/873 entries, the same as in S79/S80; [corrected in the second pass 2026-10-05: the error is NOT a constant 22.0 - predicted minus recorded is -2.0, -7.0, -15.0, -17.0, -20.0 or -22.0, the flat extras of R06, and 22.0 is only the largest]; R06 topic).

### Verification 2026-10-05 (second pass)

Method: new code `backend/scripts/research/ver2_c_stages.py` (project `verify_world` over all 85 manifest saves; U01/U02 are copies of S80/S79, so corpus-wide counts contain two duplicates), `ver2_c_identities.py` (own re-computation of the identities, prev rule, gate and ship-term counts from the parsed trade trees, exact decimal truncation), `ver2_c_gates.py`, `ver2_c_worst.py`.

Matched: `val == trunc3(max_pow x max_demand)` 866/866, 869/869, 859/859 (88,486 of 88,486 over all 85 saves); `top_power_values == val - t_out + t_in` for every pair with an entry (88,486 of 88,486 over 85 saves; the only pairs without an entry are AFA at `ethiopia` and `gulf_of_aden` in U05); `max = p_pow + sum(max_pow - prev - province_power)` 80/80, 80/80, 78/80 and 6,741 of 6,744 over 85 saves (exceptions: S64 `genua` 348.254 vs 343.254, U05 `ethiopia` 135.787 vs 133.787 and `gulf_of_aden` 562.664 vs 555.664); stage counts for `transfers` 436/436/432, `income_share` 0/368, 0/368, 0/362 checks, `retention` 0/80; `prev` rule 959/963, 963/967, 951/955.
Corrected: the `raw_power` error is not a constant 22.0 (see the note in U-R09-3): predicted minus recorded is -2.0 (256/257/248 entries in U03/U04/U05), -17.0 (147/147/145), -7.0 (51/51/52), -22.0 (42/42/42), -15.0 (20/20/21), -20.0 (6/6/6); these are the flat extras 2, 5 and 15 of R06 in combination. The AFA values in U-R09-2 are AFA with zero province power, see the R12 verification.
Unverifiable: the parser-project definitions; the cause of the 3 `max` exceptions other than U05.

## Update 2026-10-05 - Venice series U07-U30

New data: 24 saves of one game (VEN, 1.37.5, non-Ironman, 1444.11.11 -> 1445.07.02; dates and the recall / re-send history as in `R08_steering_and_link_split_response_1.md`, 'Update 2026-10-05 - Venice series'). Scripts: `backend/scripts/research/venice_b_*.py`; second pass `venice_b_v2_*.py` (raw text).

### V-R09-1 (Q8, corrects the `transfer_home_bonus` row) The rule: 0.1 per steering merchant, 0 if any merchant collects away
Claim: `countries.<TAG>.transfer_home_bonus` = 0.1 x (number of the country's merchants that steer, i.e. node entries with `type` and `has_trader`, into any link of any node) when the country has no merchant collecting away from its home node (`has_trader`, no `type`, no `has_capital`); 0.0 when it has at least one away collector. It does not require steering into the home node, and a merchant collecting at the home node does not change it. Confidence: confirmed (one controlled series + whole-world cross-section + the played saves).
Rows (VEN): U25 (1445.3.1) three steering merchants, 0.3; U26 (3.31, merchants recalled during March, no tick yet) 0.0, with the node data still showing the merchants' effect; U27 (4.1) 0.0; U28 (5.1) ragusa merchant 0.1; U29 (6.1) 0.2; U30 (7.2) 0.3. None of VEN's three merchants steers into `venice` (alexandria -> genua, ragusa -> genua, wien -> saxony). The field is refreshed at once by the merchant action (visible in U26), not at the tick.
Cross-section: all 665 countries with a home entry in U30 and in U27: `thb / 0.1 == steering merchants (0 if any away collector)` 665 of 665 (raw-text second pass; first pass: 656 of 665 with steering merchants alone, the 9 others are countries with one steering and 1-2 away merchants and thb 0.0). Table (U30 steering / away / thb): 0 / 0 / 0.0 (315 countries), 1 / 0 / 0.1 (133), 2 / 0 / 0.2 (183), 3 / 0 / 0.3 (13), 0 / 1 / 0.0 (12), 1 / 1 / 0.0 (7), 1 / 2 / 0.0 (1), 2 / 1 / 0.0 (1). Of the 329 countries with steerers and no away collector, 173 have no steerer that steers into the home node (95 with one steerer, 70 with two, 8 with three) and still have thb = 0.1 x steerers, so "into the home node" is not a condition (`venice_b_26_thb_all.py into 1445_07_02`). Played TUR saves: S79 173 of 174, S80 149/149, U03 138/138, U04 138/138, U05 135/135, U06 136/136 (the one miss: S79 three steerers, thb 0.2).
Start snapshots: U07 (1444.11.11, saved before any day passed): thb 0.0 for all 1,380 countries; U08 (11.14): 147 non-zero; U09 (11.30): 325; so the field is computed in the first days of play, not at the first tick, and start snapshots carry 0.0 because they are written before its first computation (this is the reason for "zero in all 78 start saves" in the row above).
What this corrects: response_1 Q4 row `transfer_home_bonus` ("in all 362 the country has at least one merchant steering into its home node and none collecting away; 0.1 x home-steering merchants reproduces only 102 of 362") - the count must include every steering merchant, not only those steering into the home node, and the away-collector exclusion is part of the rule; it then reproduces 869 of 870 played-save values. Source: `venice_b_26_thb_all.py` (table2), `venice_b_28_thb_played.py`; second pass `venice_b_v2_thb.py` (665 of 665 at U30 and U27).
Caveat: the maximum seen in the Venice saves is 0.3; 0.9 is the maximum of the earlier corpus (no cap tested); whether a merchant that is in transit counts: UNKNOWN.

### V-R09-2 (Q3 part, Q8) The bonus is added to `max_demand` at the home node, at the tick
Claim: at the node that carries `has_capital`, the country's `max_demand` = (its value without the bonus) + `transfer_home_bonus`, additive, and it changes only at the monthly tick. VEN rows (`max_demand` at `venice` minus at `alexandria`, same save): U07-U09 0.076 (thb 0.3 from U08 but not yet applied); U10-U13 0.376 (first tick: +0.300); U14-U26 0.377 (U26 has thb 0.0 and the old value); U27 0.077 (after the tick); U28 0.177; U29 0.277; U30 0.377. Corpus: on consecutive tick-day saves, when a country's thb changes the home `max_demand` minus the median change at its other nodes equals the change of thb (within 0.0105) in 95 of 105 cases; when thb does not change that difference is 0 in 4,544 of 4,550. Confidence: confirmed (VEN, raw-text second pass for the VEN rows), inferred for the corpus (10 misses not examined). Source: `venice_b_27_md_home.py`, `venice_b_v2_claims.py` (raw text).
Effect: see R07 response_1 'Update 2026-10-05 - Venice series' V-R07-3 (home income -37% with three merchants recalled, X unchanged).

### V-R09-3 (Q2) Envoy `action`, `num_ships_protecting_trade`, `trade_mission`
- `merchants.envoy[].action=2` is present exactly for the merchants that are placed in a node: VEN three in U07-U25, none in U26 (removed at once by the recall, mid-month, with the node data unchanged), one in U28, two in U29, three in U30 (`venice_b_v2_claims.py`, raw text). The envoy list carries only `id`, `name`, `type`, `action`; it names no node, so the link between an envoy and its node is only inferable by elimination (U28: envoy id 0 is the one placed; the only new node entry is ragusa). Confidence: confirmed.
- `num_ships_protecting_trade`: absent in U07, 3 from U08 on (the three light ships are already on a protect mission), while the node entries show ships only from the first tick: U10-U19 `ship_power` 6.0 / `light_ship` 3 at `venice`, U20-U24 at `ragusa`, U25-U30 at `alexandria` (the fleet moves along a route; the VEN entry at the node where the fleet is carries the ships). Sum of `light_ship` over VEN entries = 3 = the field in U10-U30. So the country field is live and the per-node ship data are refreshed at the tick. Confidence: confirmed for VEN. Source: `venice_b_33_ships.py`, `venice_b_1_overview.py`.
- `trade_mission`: absent in U07-U09, 0.214 (3/14) in U10-U30 for VEN whatever the merchant count (0-3) and the income; present for 193-194 countries, values of the form a/b (SWE 0.142, DAN 0.25, NOR 0.666, SHL 1.142, ALB 0.166, ATH 0.285, CYP 0.307, NAX 0.333). Not equal to envoys / (nodes with `val`, nodes with province power, collecting nodes or steering entries) for more than 3 of 200 countries. Meaning UNKNOWN. Source: `venice_b_17_mission.py`.
- `modifier` inside an entry (R09 Q1 field `modifier`): `{key="merchant_recalled" power=-10.0 power_modifier=0.0 duration=N}` appears on AI entries (TRE at `astrakhan`, HED and NJR at `ethiopia`); `duration` falls by exactly 1 per day between saves (3546 -> 3516 for 03.01 -> 03.31, 3650 -> 3630 for 12.11 -> 12.31), i.e. it counts days from 3650 (ten years); it is the only numeric entry field that changes between ticks (a new one appears with `duration` 3650 on the save of its first day: TRE at `astrakhan` in U12 1444.12.11). Permanent entry modifiers also exist: `duration` -1, `power` +20.0 (GEN at `crimea` `GEN_ITALIAN_MERCHANT_INFLUENCE`, GEN at `constantinople` `BYZ_colony_in_galata`, present from U07). VEN's own recall produced no such modifier (U26, U27). Source: `venice_b_34_recalled_mod.py`, `venice_b_25_midmonth.py`; confidence confirmed for the countdown and the two values, UNKNOWN for the trigger of `merchant_recalled`.

### V-R09-4 (data-table row on node fields) What a merchant recall changes at once and what at the tick
Claim: a recall changes immediately: the entry's `type` and `has_trader`, the country's envoy `action` and `transfer_home_bonus`; everything else - weights, `add`, `val`, `max_pow` (which keeps the merchant's +2), `max_demand`, `money`, `total`, link `incoming.add` - keeps the last tick's value until the next tick (U26 trade block differs from U25 only by those flags and three modifier durations). Source: `venice_b_16_diff.py` (U25 -> U26), `venice_b_v2_rank.py` (b). Confidence: confirmed (one recall of three merchants). The U05 `ethiopia` case (country lost its last province) is a different event and stays open.

### Verification 2026-10-05 (second pass, Venice series)
Method: `venice_b_v2_claims.py` (raw-text extraction of thb, envoy actions and `max_demand` at two nodes), `venice_b_v2_thb.py` (raw-text thb rule over all countries), `venice_b_v2_rank.py` (raw line diff).
Matched: all VEN rows of V-R09-1 and V-R09-2; the rule 665 of 665 at U30 and U27; 13 changed lines between U25 and U26.
Not independently re-computed: the played-save counts (869 of 870), the corpus tick-day table (95 of 105 / 4,544 of 4,550), the ship and `trade_mission` observations, the `merchant_recalled` countdown.
Unverifiable: the game names and definitions of these fields (no parser-source lookup in this round).

## Data basis (2026-10-06)

On 2026-10-06 the research data was rebuilt (`docs/research/data_audit.md`): only **clean** saves are kept (the 1st of a month after the game's first trade computation, none of the player's merchants or fleets on the way; R12 final). Kept: U04 (TUR 1691.11.01), U10, U14, U20, U25, U27, U28, U29 (VEN 1444-1445). Removed: the 78 start snapshots S01-S78 and U07-U09 (saved before the first computation: steering weights, `add` and other computed fields are placeholders there) and 21 mid-month saves (S79, S80, U01-U03, U05, U06, U11-U13, U15-U19, U21-U24, U26, U30: numbers from the last 1st, merchant/ship flags from the save day). Counts above that include removed saves are kept as recorded but are **unverified on clean data** unless listed as re-checked below. Clean-data stage results quoted here: `scripts/verify_all.sh` on the 8 kept saves (calc 0.2.0).

- Field identities were counted over all saves (mostly start snapshots): unverified on clean data, except the stage identities re-checked on the 8 kept saves: `val`, `retention`, `current`/`outgoing`, `power_fraction`/`total` exact; `prev` rule 28 failures of 16,140.


## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R09-1 Fields confirmed by single changes
- `merchants` / envoys: +1 merchant modifier (E13) raises the envoy count 3 -> 4 at once. Confirmed.
- `transfer_home_bonus`: 0.000 as soon as one merchant collects away (P03); unchanged (0.200) when the ragusa steerer steers away from the home node (P01); a steerer at constantinople, which has no link into the home node, adds nothing (P04). See R01 V2-R01-4. Confirmed (P03), inferred (counting rule).
- `top_power` of a country that lost its last province keeps it until the next 1st (E21, NAX: alexandria 2.046, constantinople 9.579 on 12.03 and 12.15). Confirmed.
- `has_capital` (E19): capital and trade port moved together within the venice node; not decided which one it follows.

## Update 2026-10-08 - experiment round 2

Source: 27 single-change jobs run in the game by the automation (`tools/EU4-game-automation/experiments/round2/`: `PLAN.md`, `RESULTS.md`, scripts `analysis/`); saves under `round2/out/<id>/` (t1 = 1445.1.1, t2 = 1445.2.1; all dated, player and plain text checked). Controls as in round 1 (E01c / E01d on the E00 base) plus R2-C-U10, R2-H-MAM-C, R2-H-TUR-C, R2-C-NED18. **Void:** every merchant recall by save patch (R2-B5a, R2-B4, R2-B5c, R2-H-MAM-B1, R2-H-TUR-B1 and the recall half of R2-B5b / R2-H-MAM-B2): the patched save has no merchant at the node, t1 has it again (cause unknown); the embargo (R2-EMB) and privateer (R2-PRIV) patches are dropped on load; R2-TC added nothing (no territory province). No claim below rests on a recall.

### V4-R09-1 `has_capital` follows `trade_port`; `transfer_home_bonus` is stored
Claim: R2-PORT (only the trade port moved) moves `has_capital` (V4-R02-1); `transfer_home_bonus` is a stored country field used as written for two months (V4-R01-3). Confidence: confirmed / inferred (update rule).
