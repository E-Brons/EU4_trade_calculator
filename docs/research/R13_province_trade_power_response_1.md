# R13 response 1 - Province trade power and local value (data-derived points only)

Scope: only the points of `R13_province_trade_power_request_1.md` that the 82 fixture saves can settle. Each claim comes from a script run (`backend/scripts/research/r09_r13_*.py`, named per claim) over the `provinces` and `trade` blocks of the saves; `confirmed` = whole corpus tested with counts and exceptions listed, otherwise `inferred`. Anything needing an outside source is listed at the end. Note: U02 = same date as S79 and U01 = same date as S80, with identical numbers, so the played saves (S79, S80, U01, U02, not saved on the 1st) are two distinct saves counted twice.

---

## Q1 - One trade value formula and `local_value`

### C-01 `local_value` from goods produced and prices
Claim: `local_value` (ducats per month) `= sum over the 33 goods i of trade_goods_size[i] * current_price[i] / 12`, where `current_price[i]` is read from the save's own top-level `change_price={ <good>={ current_price=... } }` block (the key order of that block is the index order of `trade_goods_size`). The division by 12 is in the data: a yearly price 2.5 shows as 0.2083 per unit.
Formula: as stated. Goods order: `nogoods, grain, wine, wool, cloth, fish, fur, salt, naval_supplies, copper, gold, iron, slaves, ivory, tea, chinaware, spices, coffee, cotton, sugar, tobacco, cocoa, silk, dyes, tropical_wood, livestock, incense, glass, paper, gems, coal, cloves, unknown`. `gold` has price 0.0 in the save and contributes nothing.
Applies when: all 82 saves.
Source: save corpus, `r09_r13_goods.py` (index mapping and a least-squares price fit), `r09_r13_prices.py`, `r09_r13_prices2.py`, `r09_r13_localvalue.py`.
Quote: S42 `change_price={ nogoods={ current_price=1.000 } grain={ current_price=2.000 ...` and `wine={ current_price=3.125 ...`; the least-squares fit of `local_value` against `trade_goods_size` in S42 returns grain 2.0, wine 3.125, cloth 4.2, fur 3.5, i.e. the saved prices (x 1/12). In S01 the fit returns grain 0.208, cloth 0.25, fur 0.167, ivory 0.334, cloves 0.666, paper 0.292 = 2.5, 3, 2, 4, 8, 3.5 divided by 12 (the goal's price list).
Confidence: confirmed with the exception below: over 6,502 nodes, 5,748 reproduce to 0.002 ducats using `change_price`; the remaining 754 are 742 nodes that contain incense and 12 nodes in the played saves (`hormuz`, `white_sea`, `genua`, each in S79/U02 or S80/U01).
Caveats / exceptions:
- Incense: in every node with incense (except `australia`, see below) the real `local_value` is higher than the formula. Independent recount (start saves, 746 nodes with incense): the premium per unit equals exactly 10% of that save's incense price, i.e. incense is valued at `1.1 x current_price`: 702 of 746 nodes fit to 0.002 ducats with it. The implied extra per unit (x 12) is 0.25 where the save price is 2.5 (40 saves), 0.2125 at 2.125 (26 saves) and 0.30 at 3.0 (16 saves), so it is not a flat +0.25. The 44 nodes that do not fit are all `australia` (0.6 incense), where the plain `change_price` fits (44 of 44). The save says `incense current_price = 2.5` (2.125 in 26 saves, 3.0 in 16); why incense carries a 10% premium (and not in `australia`) is UNKNOWN. With the goal's table price 2.5 and no premium the 1444 saves S01-S35 are wrong by up to 0.109 ducats (`gulf_of_aden`: 4.952 stored vs 4.848, difference 0.104); with 2.75 for incense they match to 0.0125 (one node, `australia` 1.375 vs 1.388).
- The goal's price table is valid only for the 1444 start saves. Later saves have other prices in `change_price` (S42: grain 2.0, wine 3.125, cloth 4.2 ...; S37 copper 4.5, paper 5.25), so `local_value` cannot be computed from the goal's table outside 1444.
- Played saves: 3 nodes per save fail (above), the sizes/prices there are stale between ticks (inferred, not tested).
- `trade_goods_size[i]` is about `0.2 * sum of base_production` of the provinces with `trade=<node>` and `trade_goods=<good>` in the 1444 saves (independent recount: median ratio to `0.2 * base_production` is 1.00 for 29 of 30 goods in S01, S14 and S36; cloves 1.1, i.e. 0.22). In the later saves S42 and S60 the ratio is 1.02-1.2 for most goods, so the plain 0.2 rule does not hold there. Province modifiers to goods produced are not visible; the rule beyond 0.2 x base_production is UNKNOWN. Note: `tradegoods_total_produced` (top-level, 33 numbers) equals the sum of `trade_goods_size` over all nodes for every index except the last (`unknown`, which has no node share: e.g. -279.84 difference in 35 saves; the index-only statement holds in 82 of 82 saves).

---

## Q3 - Is `province_power` the plain sum of the provinces' `trade_power`?

### C-02 `province_power` is the sum over provinces that the country **controls**, not owns
Claim: the `province_power` of country C at node N equals the sum of the stored `trade_power` of all provinces with `trade=N` and `controller=C` (a province occupied by another country counts for the occupier; a province held by rebels counts for nobody).
Formula: `province_power(C,N) = sum over provinces p with p.trade=N and p.controller=C of p.trade_power`.
Applies when: all entries; tolerance 0.0005 per summed province (the display rounding of the save).
Source: save corpus, `r09_r13_provpow.py`, `r09_r13_provpow2.py`, `r09_r13_provpow3.py`, `r09_r13_provpow4.py`, `r09_r13_occupied.py`.
Quote: S01 `gujarat` MER: `province_power=22.494`; owned provinces sum to 23.09, of which `-514 Marwar` has `owner=MER controller=REB trade_power=0.596`; 23.09 - 0.596 = 22.494. S79 `champagne`: provinces `owner=GBR controller=FRA` are counted in FRA's entry, not GBR's.
Confidence: confirmed. Entry-node pairs tested: 53,944. Owner basis fails 741 times, controller basis 320 times (independent recount, same pair set and tolerance; the 876 and 376 of the first version of this text used other pair sets and could not be reproduced); after excluding rebel-held provinces (no entry exists for `REB`) and allowing display rounding the controller basis fails **320 of 53,944 (0.6%)**: 310 in the played saves (S79 88, U02 88, S80 67, U01 67) and 10 in start saves, all with a whole-number surplus in the entry (S43 `mexico` C01 +1.0; S56/S59/S60 `patagonia` C05 +1.0; S65/S66 `patagonia` C05 +5.0 and `laplata` +3.0; S72 `amazonas_node` COL +2.0, `carribean_trade` COL +5.0): a flat integer in the entry (all colonial-nation tags, C01/C05/COL) that is not in any province's `trade_power`; cause UNKNOWN.
Occupation: of 792 occupied provinces (controller is neither the owner nor REB, trade_power > 0) the owner's entry equals the owner's sum **including** the occupied province in 0 cases; the controller's entry equals the controller-basis sum in 658. In the start saves it holds in 580 of 580; in the played saves only in 78 of 212 (the played saves are not at a tick; inferred).
Rebels: provinces with `controller=REB` are in no entry. They are in the node's `p_pow` and `total` (283 nodes in the corpus: S01 `gujarat` 0.596, `ethiopia` 0.388, `gulf_of_aden` 0.594 ...), see the R09 response, C-06 and C-10.
Not tested (fields not found): trade-company ownership and blockade; there is no province key for them that I identified in these saves.

Also `highest_power` of a node = the largest single province `trade_power` in it (6,480 of 6,504; the 24 failures are in the played saves).

---

## Q4 / Q5 - What the stored province `trade_power` contains; real test rows

### C-03 Structure of the stored province `trade_power`
Claim: `trade_power = (0.2 * development + centre_of_trade_flat) * M * (1 - 0.005 * local_autonomy)` with `development = base_tax + base_production + base_manpower`, `centre_of_trade_flat` = 5 / 10 / 25 for `center_of_trade` 1 / 2 / 3 (0 if absent), and `M` an additive multiplier (`1 + sum of local and global modifiers`) that is **not** stored per province. The autonomy factor is approximate: the data suggest about 0.0051 per autonomy point (0.005 is within 0.04%).
Source: save corpus (S01 and S14, identical province data), `r09_r13_provtp.py`, `r09_r13_provtp2.py`.
Quote (S01, all provinces of MER at `gujarat`, M = 1.2):
- `-2058 Mewar` dev 9, no CoT, autonomy 0: `0.2*9*1.2 = 2.16`, stored `trade_power=2.16`.
- `-518 Chittor` dev 5, `center_of_trade=1`, autonomy 0: `(1.0 + 5)*1.2 = 7.2`, stored 7.2.
- `-2087 Ajmer` dev 8, CoT 1, `local_autonomy=1.0`: `(1.6+5)*1.2*0.995 = 7.8804`, stored 7.88.
- `-2067 Gorwar` dev 9, autonomy 2.0: `1.8*1.2*0.99 = 2.1384`, stored 2.138.
- `-4506 Barmer` dev 3, autonomy 1.0: `0.6*1.2*0.995 = 0.7164`, stored 0.716.
Rows with M = 1.45: `-1 Stockholm` (SWE, `baltic_sea`) dev 14, CoT 2, autonomy 0: `(2.8+10)*1.45 = 18.56`, stored 18.56; `-23 Bergenhus` (NOR, `north_sea`) dev 7, CoT 2: `(1.4+10)*1.45 = 16.53`, stored 16.53. Rows with CoT 3 and autonomy: `-568 Chittagong` dev 13, CoT 3, autonomy 6: `(2.6+25)*1.45*0.97 = 38.819`, stored 38.805; `-4457 Khambhat` dev 11, CoT 3, autonomy 5: `(2.2+25)*1.45*0.975 = 38.454`, stored 38.433 (deviation 0.04-0.05%).
Confidence: confirmed for the shape `(0.2 x dev + CoT flat) x M` with the CoT flats 5 and 10 (exact rows above; the CoT 25 rows deviate by 0.04-0.05% through the autonomy term). `M` classes in S01 (2,469 provinces with a positive base and controller = owner; M rounded to 0.1): 1.2: 1,443; 1.4 (=1.45): 591; 1.3: 137; 1.5: 122; 1.7: 34; 1.8: 29; 1.6: 23; others fewer. So most provinces have exactly `M = 1.2`, i.e. a `+20%` that applies to all of them, and the other values differ by 0.1, 0.25, 0.3, 0.55 steps: additive, not multiplicative (1.2 + 0.25 = 1.45 and not 1.2 x 1.25 = 1.5; this remark is inferred: a class at 1.5 exists too, 122 provinces, which would also fit 1.2 x 1.25).
Inferred only: the M = 1.45 provinces lie in coastal trade nodes (nippon 52, malacca 42, lubeck 29, north_sea 29, gulf_of_aden 29, mexico 28 ...) while M = 1.2 provinces lie in inland nodes (samarkand 50, kiev 46, timbuktu 43, yumen 41, ethiopia 40 ...), so the +0.25 is probably the coastal bonus; I did not test it against a coastal flag (there is none in the province block). What produces the base +0.2, the +0.1 / +0.3 / +0.55 steps (buildings, estuary, marketplace, country modifiers) and the order "base x (1 + local + global)" vs product: UNKNOWN. The goal's +25 for CoT 3 and the +5/+10 for CoT 1/2 match the rows above.
Provinces with the key `buildings` are mostly only `fort_15th` in the 1444 saves, so building effects cannot be read from this corpus start state; the later saves were not analysed (not finished).

### Q5 - Replacement of invented test cases
The rows in C-03 are real rows (province ids, owners, nodes, stored values quoted from S01). Stored example `trade_power=41.670` of the goal is not identified in any save, so it is not used. Fields needed for a full recomputation and absent from the save: the country's local and global trade power modifiers (mercantilism effect, ideas, policies), the coastal flag, the building effect per level.

---

## Not answered (needs an outside source or analysis not finished)

- Q1: a game-file/wiki source for `trade_goods_size` units and `trade_value_modifier`; the +0.25 extra for incense; price change mechanics beyond what `change_price` stores (it stores `change_price={ key= value= expiry_date= }` entries per good: e.g. S42 grain `COLUMBIAN_EXCHANGE value=-0.200 expiry_date=1821.1.2`; not analysed further).
- Q2: caravan power (`CARAVAN_FACTOR`, `CARAVAN_POWER_MIN/MAX`): not visible in the saves; no test possible.
- Q4: wiki/defines quotes for each modifier (development 0.2, CoT levels, mercantilism +2% per point, estuary, buildings, trade company +100%) and the order of local/global modifiers; the composition of `M` (analysis of what makes 1.2 / 1.3 / 1.5 / 1.75 not finished).
- Q6: trade company region effect, merchant republic bonus, blockade, siege, trade company goods produced bonus: not tested (analysis not finished); only occupation (C-02) and rebels (C-02) are settled.

---

## Verification (date 2026-10-04)

Independent recomputation (new code, not the author's logic): `backend/scripts/research/ver_r13_prov.py` (province sums, `p_pow`, `highest_power`, occupation), `ver_r13_quotes.py` (quoted province rows, M classes), `ver_r13_localvalue.py` and `ver_r13_incense.py` (`local_value` from the saves' own `change_price`), `ver_r13_goods.py` (price quotes, size vs base production). All run over the 82 saves.

**Matched (claim and numbers reproduced):**
- C-01: goods order identical in all 82 saves; 6,502 nodes with `local_value` and `trade_goods_size`, 5,748 fit to 0.002, 754 do not (742 with incense, 12 played-save nodes `hormuz`, `white_sea`, `genua` x4 played saves); gold price 0 in 82 of 82; S42 prices (grain 2.0, wine 3.125, cloth 4.2, fur 3.5) and S01 prices (grain 2.5, cloth 3, fur 2, ivory 4, cloves 8, paper 3.5); S37 copper 4.5, paper 5.25; incense save price 2.5 / 2.125 / 3.0 in 40 / 26 / 16 saves; `gulf_of_aden` 4.952 vs 4.848; `tradegoods_total_produced` differs from the node sum only at index 32 in 82 of 82 saves.
- C-02: 53,944 entry-node pairs; controller basis fails 320 (S79 88, U02 88, S80 67, U01 67, start saves 10 with the listed whole-number surpluses); 283 rebel nodes; 792 occupied provinces, 0 owner-basis matches, 658 controller-basis matches, 580 of 580 in start saves, 78 of 212 in played saves; `highest_power` 6,480 of 6,504 with the 24 failures all played; S01 `gujarat` MER 22.494 (owned sum 23.09, `-514` Marwar REB 0.596).
- C-03: every quoted province row (Mewar, Chittor, Ajmer, Gorwar, Barmer, Stockholm, Bergenhus, Chittagong, Khambhat) reproduces with the stated inputs; the implied M is 1.20 / 1.20 / 1.1999 / 1.1998 / 1.1993 / 1.45 / 1.45 / 1.4495 / 1.4492 with factor `1 - 0.005 x autonomy`; M classes in S01 (2,469 provinces: 1,443 / 591 / 137 / 122 / 34 / 29 / 23); the median implied M falls about 0.0051 per autonomy point.

**Corrected (old -> new, why):**
- C-01 incense: "priced about 0.25 above `change_price`, flat" -> a 10% premium on the save's incense price (`1.1 x current_price`): 702 of 746 start-save incense nodes fit to 0.002; the 44 that do not are all `australia`, where the plain price fits (44 of 44). The implied extra scales with the save's price (0.25 at 2.5, 0.2125 at 2.125, 0.30 at 3.0), so it is not a constant; the reason stays UNKNOWN. Maximum error of the plain formula over S01-S35 is 0.109 (not 0.104, which is the `gulf_of_aden` row).
- C-01 goods size: "median ratio 0.200 for 29 goods in S01, S14, S36, S42, S60" -> true only for S01, S14, S36 (cloves 1.1); S42 and S60 have most goods at 1.02-1.2. "cocoa 0.2012" not reproduced, removed.
- C-02: "owner basis fails 876, controller basis 376" could not be reproduced under any single definition; replaced by the recount with the final pair set: owner 741, controller 320.
- C-03: the remark "additive, not multiplicative" downgraded to `inferred` (a class at 1.5 also exists, 122 provinces, consistent with 1.2 x 1.25).

**Could not be verified / not re-tested:** the coastal-node lists for M = 1.45 vs 1.2 (nippon 52, malacca 42, ..., samarkand 50, ...), which are `inferred` in the response; the 310 played-save failures were counted but their cause (stale between ticks) is not tested; the statement that start-save surpluses are "a flat integer in no province's trade_power" is reproduced as a count but its mechanism stays UNKNOWN; the sentence on `trade_company` ownership and blockade fields not being found cannot be checked by a positive test.

## Update 2026-10-05 - Venice series U07-U30

Data: the Venice series U07-U30 (player VEN, game 1.37.5, non-Ironman plain-text saves, same mod list as S01, new campaign started 1444.11.11): U07 1444.11.11, U08 11.14, U09 11.30, U10 12.01, U11 12.02, U12 12.11, U13 12.31, U14 1445.01.01, U15 01.02, U16 01.15, U17 01.24, U18 01.30, U19 01.31, U20 02.01, U21 02.03, U22 02.10, U23 02.17, U24 02.28, U25 03.01 (U07-U25: no player action at all); then U26 03.31 (all three VEN merchants recalled during March), U27 04.01, U28 05.01 (ragusa merchant sent again), U29 06.01 (alexandria), U30 07.02 (wien). Scripts: `backend/scripts/research/venice_a_*.py` (loader `venice_load.py`), second pass `venice_a_ver.py` (raw text diff of the `trade` block, own Decimal loop for `prev`).

### V-R13-1 `province_power` equals the controlled-province sum on the 1st, and drifts in between
Claim: C-02 (`province_power` of C at N = sum of stored `trade_power` of the provinces with `trade=N`, `controller=C`) holds for 100 % of the entries in every save written on a 1st or right at the start, and only for 63-98 % in the other saves, because the provinces' stored `trade_power` moves on days other than the 1st while the node entries stay frozen.
Source: `venice_a_r13.py`.
Quote (entries equal / entries): U07 (1444.11.11) 773/773; U08 (11.14) 756/773; U09 (11.30) 743/773; U10 (12.01) 773/773; U11 (12.02) 749/773; U12 (12.11) 721/773; U13 (12.31) 709/773; U14 (1445.01.01) 773/773; U15 (01.02) 513/773; U16-U19 510-511/773; U20 (02.01) 773/773; U21 (02.03) 611/773; U22-U24 606-610/773; U25 (03.01) 772/772; U26 (03.31) 484/772; U27 (04.01) 772/772; U28 (05.01) 772/772; U29 (06.01) 772/772; U30 (07.02) 512/772. Provinces whose stored `trade_power` changed since the previous save: 122 (U07 -> U08), 18 (U08 -> U09), 0 (U09 -> U10), 53 (U10 -> U11), 33, 25, 0 (U13 -> U14), 962 (U14 -> U15, 1.1 -> 1.2), 12, 3, 1, 0, 0 (U19 -> U20), 525 (U20 -> U21, 2.1 -> 2.3), 1, 5, 3, 0 (U24 -> U25), 1,045 (U25 -> U26, 3.1 -> 3.31), 1 (U26 -> U27), 51 (U27 -> U28), 954 (U28 -> U29), 1,038 (U29 -> U30). In U14 -> U15 the provinces that changed differ only in `trade_power` (no change of `local_autonomy` or development), so the stored province value is recomputed on days of its own, not with the node tick.
Confidence: confirmed. This tests the earlier inference ("played-save failures of `province_power` are mid-month staleness"): confirmed by the 1st-of-month saves of a controlled game.
Caveats: the day on which the provinces are recomputed is not visible with the saves taken (962 provinces move between 1.1 and 1.2, 1,045 between 3.1 and 3.31, 525 between 2.1 and 2.3); the cause of the changes (autonomy change at the 1st shows in `local_autonomy` of 1,209 provinces between U24 and U25 without a change of `trade_power`) is not analysed here.

### V-R13-2 Not settled by this series
Composition of `M`, building effects, trade company region, blockade, mercantilism, incense: no intervention of that kind was made; the R13 request_2 rows stay.

### Verification 2026-10-05 (second pass)
V-R13-1 was checked by two paths: `venice_a_r13.py` (parsed `provinces` block) and the equal 773/773 at the 1st against the node-side `province_power` field classes in `venice_a_fields.py` (`province_power` changes only on the 1sts: 262 fields U19 -> U20, 167 U24 -> U25, 289 U26 -> U27).
