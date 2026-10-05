# R07 response 1 - Income formula, merchant-present bonus, trade efficiency

Only data-settled points. Scripts: `backend/scripts/research/r07_r08_r12_income.py`, `income2.py`, `x1444.py`. X = money/total - 1 is computed with an interval (money and total are 3-decimal truncated): X in `[money/(total+0.001) - 1, (money+0.001)/total - 1]`.

Corpus limit (important): the 78 start snapshots contain **only home-node collectors** (36,366 entries with merchant + 5,742 without; 0 collecting entries away from the capital). Away collecting merchants exist only in S79 and S80 (99 entries [stale: U03-U05 also contain them, see the second-pass verification below]; U01/U02 are the same data), so every away/home test rests on two played saves.

## Q1 - Merchant-present rule
Claim C-01 (confirmed as data): pairs (same country, same save, home X vs away X with `has_trader`, both totals >= 3): home node without merchant: 16 of 16 pairs give away - home = +0.10 (interval contains 0.10); home node with merchant: 28 of 28 pairs give 0.00. (Verification: U01/U02 duplicate S80/S79, so these are 8 and 14 distinct pairs; home without merchant = HAB, TUR, BRI; home with merchant = BRI, CSH, DEC, GEN, GZI, PAP, SPA.) Source: S79, S80 (`income.py`). Quote: TUR S79 constantinople money 123.313 total 70.465 (no merchant) vs ragusa 4.371/2.363 and venice 20.729/11.205 (merchant); S79 GEN home genua `has_trader` X 0.82 vs champagne 0.82 and venice 0.82; S79 PAP home venice (no merchant) 0.87 vs genua 0.969.
Rules compared on all 198 away entries (99 distinct, U01/U02 being copies; the counts below are the 198-entry counts, halve them for distinct entries) with a collecting home entry (X of the country taken from the home entry, bonus 0.10 where the rule says so; `income2.py`): M "+0.10 whenever `has_trader` (any node, home included)" fits 134/134 (home merchant) and 64/64 (home without merchant); N "+0.10 only when away, with merchant, and the home node has no merchant" fits 134/134 and 64/64; A "+0.10 whenever away with merchant" fits 64/64 but fails 134/134 of the home-merchant group; Z "never" fails 64/64. M and N cannot be told apart by pairs. The project's `rule_merchant_bonus(has_trader)` is M and is not contradicted by any pair; the goal's reading that M is refuted by the cross-section is not proven, because that compares different countries.
Cross-section (home entries with total >= 0.4, median X): start snapshots: merchant vs none S01 0.069 vs 0.070, S36 0.089 vs 0.090, S37 0.159 vs 0.180, S38 0.249 vs 0.250, S42 0.269 vs 0.290, S78 0.269 vs 0.270 (no shift of 0.10 at home); played saves: S79 0.45 vs 0.37, S80 0.52 vs 0.419 (shift 0.08-0.10, confounded by country size). So: start snapshots favour "no home bonus" (N), played saves favour M; UNKNOWN. What settles it: one country with a merchant at home whose merchant is recalled (or added) with everything else unchanged (intervention pair), reading X at home before/after.
Rejected: the draft's rule as stated (+0.10 at home for every `has_trader`) is not refuted by the pairs; its 1444 explanation (see Q4) is not supported.
**Updated 2026-10-05:** U03-U05 contain the first same-country change (TUR adds a home merchant, U04 -> U05) and a second one (YEM); both rules still fit and the verdict stays UNKNOWN (section Update, U-1).

## Q3 - Truncation (data part)
Claim C-02 (confirmed): `money = trunc3(total * (1 + X))`, not rounding. Source: 103 collecting entries with total >= 20 (X fits a 0.01 grid within 0.0006 in all 103): truncation reproduces 103 of 103; in the 56 where truncation and rounding differ, truncation matches 56 of 56, rounding 0 (same result on the 80 distinct saves: 85 of 85 and 46 of 46). Rows: 2.363 x 1.85 = 4.37155 -> stored 4.371 (rounding would give 4.372); 70.465 x 1.75 = 123.31375 -> 123.313; 11.205 x 1.85 = 20.72925 -> 20.729.
Node effects: the 99 away entries fit the rules above with no extra term; 81 are in `trade_company_region` nodes and 18 not; none in a node with privateer power (`collector_power_including_pirates > collector_power`). So a trade-company node effect on `money` is not seen; tariffs, privateers and embargo: no instance -> UNKNOWN.

## Q4 - 1444 start values (data part)
Source: S01 (all 1444 saves share the world), 202 home collectors with total >= 0.4, joined with the `countries` block (`x1444.py`).
- Distribution of X at home: 0.07 (108 countries), 0.12 (28), 0.17 (16), 0.02 (13), 0.01 (12), 0.05 (14), 0.27 (6), 0.22 (2), 0.32, 0.37 (one each), 0.15 (ZIM) = 202.
- Technology: adm/dip/mil levels are always equal in 1444 (181 at 3/3/3, 12 at 2/2/2, 9 at 1/1/1), so which tech matters cannot be separated. Level 3: 0.07 is the modal value (108 of 181); level 2: 0.05 (10 of 12); level 1: 0.01 (5) or 0.05 (4).
- Government reform (level 3, mercantilism 10 unless noted): `plutocratic_reform` 0.12 in 11 of 11; `steppe_horde` 0.02 in 11 of 11; `signoria_reform` (mercantilism 25) 0.12 in 3 of 3; `free_city` (25) 0.27 x6, 0.32, 0.37; `merchants_reform` 0.17/0.22/0.22; `feudalism_reform` 0.07 in 31 of 32 (SWE 0.12); `iqta` 0.07 in 12 of 14.
- Steps of 0.05 between countries with identical reform, religion and tech (e.g. SWE 0.12 vs DAN 0.07, BRA 0.12 vs 0.07 peers) are not explained by any country field in the save (no modifier list is stored for 1444 countries) -> UNKNOWN.
- The home merchant is not the cause of 0.07/0.17: at X 0.07 there are 53 countries with and 55 without a merchant.
- The draft's "0.07 includes a merchant bonus" is contradicted by the previous bullet.

## Q5 - Validation
Reproduced (goal rows, truncation): TUR constantinople 70.465 x 1.75 = 123.31375 -> 123.313; ragusa 2.363 x 1.85 = 4.37155 -> 4.371; venice 11.205 x 1.85 = 20.72925 -> 20.729. On the 16 + 28 country pairs (total >= 3; 8 + 14 distinct): rule M/N reproduce all 44; A fails the 28 home-merchant pairs; Z fails the 16.

## Not answered (needs an outside source)
Q2 every item of the Ottoman efficiency table (tech, ideas, policies, reforms, privileges), Q3 whether tariffs/embargo enter the formula by source, Q6 provenance of quotes. Not answered (analysis not finished): a decomposition of the 0.05 steps in Q4 and a test of M vs N.

## Verification (date 2026-10-04)
Independent recomputation (new code, no shared logic with the author's scripts): `backend/scripts/research/ver_common.py`, `ver_r07.py`, `ver_r07b.py`, `ver_r07c.py`, `ver_r07d.py`. U01/U02 are byte-identical in trade content to S80/S79, so every count over "82 saves" double-counts the two played saves; distinct counts are given where they differ.

Re-run and matching:
- `money = trunc3(total x (1+X))`: 103 of 103 and 56 of 56 reproduced (82-save count); on the 80 distinct saves 85 of 85 and 46 of 46, rounding 0.
- Quoted rows (S79): TUR constantinople 123.313 / 70.465, ragusa 4.371 / 2.363, venice 20.729 / 11.205; GEN genua, champagne, venice X 0.82; PAP venice X 0.87 (home, no merchant), genua 0.969.
- Away collectors: 99 distinct entries, 81 in `trade_company_region` nodes, 18 not, none in a node with `collector_power_including_pirates > collector_power`.
- Rule table (M, N, A, Z): same pattern as reported (M and N fit everything, A fails the home-merchant group, Z fails the home-without-merchant group); distinct counts 67/67 and 32/32 instead of 134/134 and 64/64.
- Cross-section medians (S01, S36, S37, S38, S42, S78, S79, S80): all 8 pairs of values reproduced to the third decimal.
- 1444: 202 home collectors; tech triples 181 / 12 / 9; level-3 modal 0.07 (108), level 2 0.05 (10 of 12), level 1 0.01 (5) or 0.05 (4); `plutocratic_reform` 0.12 (11 of 11), `steppe_horde` 0.02 (11 of 11), `signoria_reform` 0.12 (3 of 3), `free_city` 0.27 x6 / 0.32 / 0.37, `merchants_reform` 0.17 / 0.22 / 0.22, `feudalism_reform` 0.07 (31 of 32 at tech 3; SWE 0.12), `iqta` 0.07 (12 of 14 at tech 3); 53 countries with and 55 without a home merchant at X = 0.07; SWE 0.119 vs DAN 0.07, BRA 0.119 (the three have mercantilism 10, so mercantilism does not explain the step).

Corrected:
- Pair counts 16 and 28 -> 8 and 14 distinct pairs (double counting of U01/U02). The home-without-merchant evidence rests on three countries (HAB, TUR, BRI), the home-with-merchant evidence on seven (BRI, CSH, DEC, GEN, GZI, PAP, SPA); BRI is in both groups (S79 with, S80 without a home merchant).
- "198 away entries" -> 99 distinct (rule counts 134/64 -> 67/32).
- 1444 distribution: `0.01` 9 -> 12 and `0.22` 3 -> 2 (the listed counts summed to 200; the correct counts sum to 202).

Could not be verified: the points under "Not answered" (outside sources). Labels: C-01 "confirmed as data" and C-02 "confirmed" stand; the M-versus-N question stays UNKNOWN as written.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below come from one run each of the scripts `backend/scripts/research/u345_home_*.py` (and `u345_ships_*.py` where stated). Unlike the Verification section above they have not been re-computed by an independent verifier. Labels: `confirmed` = whole set with exceptions listed, `inferred` = otherwise.

New data: U03 (1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign as S79 (1665.4.22) and S80 (1682.4.18). They are not independent of S79/S80 or of each other.

### U-1 Merchant rule M versus N on same-country changes (updates Q1)
X = money / total - 1. TUR, home node constantinople / away nodes with a merchant (total >= 3):

| Save | Date | Home X | Away X | Merchant at home |
|---|---|---|---|---|
| S79 | 1665.4.22 | 0.75 | 0.85 | no |
| S80 | 1682.4.18 | 0.82 | 0.92 | no |
| U03 | 1691.1.9 | 1.02 | 1.12 | no |
| U04 | 1691.11.1 | 1.07 | 1.17 | no |
| U05 | 1693.4.15 | 1.07 | 1.07 | **yes (new)** |

- Pairs (away X - home X, total >= 3): U03 home without merchant +0.10 x 6, home with merchant 0.00 x 10; U04 6 / 8; U05 home with merchant 0.00 x 14, home without merchant +0.10 x 2. Nothing against M ("+0.10 whenever `has_trader`") or N ("+0.10 only away, with a merchant, and no merchant at home"): both fit every pair. The same countries recur across the saves, so these are not independent counts.
- **TUR U04 -> U05 (home merchant added at constantinople):** home X unchanged (1.07 -> 1.07), every away X lowered by 0.10 (1.17 -> 1.07). Under N this is "base unchanged". Under M it needs the base to fall by exactly 0.10 in the same interval. TUR's modifier list changed in that interval (`trade_success`, expiry 1693.3.21, removed; `discontent_sowed`, expiry 1696.11.6, and `dip_boost`, expiry 1703.3.20, added); ideas, government reforms, technology levels, mercantilism (30) and estate loyalty tiers are unchanged. The trade-efficiency effect of those three modifiers is not in the save, so the pair does not decide between M and N.
- **YEM gulf_of_aden (U04 -> U05), a second home-merchant addition:** home X 0.42 -> 0.52 (+0.10) with no change in ideas, reforms or technology; the modifier `old_rights_granted_to_nobility` was added. This agrees with M; N would need another +0.10 source. [qualified in the second-pass verification below: YEM's home X also rose by 0.10 in the previous interval without a merchant change] Earlier cases over nine years (S80 -> U03: BLG venice merchant removed -0.10, SND gujarat removed -0.10, HUN pest merchant added -0.10, the wrong sign for M) had ideas changing in each and are not used.
- **Unobserved inputs:** among the countries where nothing visible changed (merchant at home, ideas, reforms, diplomatic technology, modifier names), home X still changes in 6 of 22 (U03 -> U04) and 5 of 14 (U04 -> U05) countries. So a before/after of a single country cannot isolate the merchant term. The idea "estate loyalty >= 60 adds +0.05" (TUR U03 -> U04 +0.05 coincided with estate 0 crossing 60) is contradicted by RUS (two estates fall below 60, X change 0.0), GEN (one, 0.0) and SND (0.0).
- Verdict: M versus N is UNKNOWN. Confidence: the table and counts are inferred data (single run). What settles it: the trade-efficiency effects of `trade_success`, `discontent_sowed`, `dip_boost` (TUR) and `old_rights_granted_to_nobility` (YEM): if `trade_success` + `discontent_sowed` net to -0.10 and `dip_boost` is 0, TUR fits M and YEM fits M; if they net to 0, TUR fits N and YEM needs another cause.

Updated 2026-10-05: save U06 (1696.3.25) adds a sixth TUR point (home 1.12, away 1.12, both merchants present) and a tech-step test across all countries; see 'Update 2026-10-05 - save U06' at the end. It does not decide M versus N.

### U-2 TUR changes between consecutive saves (data for Q1 of request_2)
- S80 -> U03 (9 years): technology +1 (adm 22, dip 22, mil 23), prestige, estate influence modifiers, `trade_embargoed_by` set, modifiers `khalifah`, `sect_practices`, `muslim_enforced_religion`, `trade_success` (expiry 1693.3.21) and others; home X 0.82 -> 1.02.
- U03 -> U04: `discontent_sowed` (expiry 1691.5.6) gone, `mecca_timer` and `pious_ruler` appear, estate 0 loyalty 57.8 -> 66.7, spy_ideas 0 -> 1, ships protecting trade 149 -> 89; home X 1.02 -> 1.07.
- U04 -> U05: as in U-1; ships 89 -> 109.

### Verification 2026-10-05 (second pass)

Independent code (new, not reusing the author's logic): `backend/scripts/research/ver2_b_lib.py`, `ver2_b_tur.py`, `ver2_b_bonus.py`, `ver2_b_resid.py`, `ver2_b_x.py`, `ver2_b_switch.py`, `ver2_b_corpus.py`; corpus of 85 saves (S01-S80, U01-U05; U01/U02 copy S80/S79). Each Update claim was re-run and recomputed. Labels follow the rule confirmed = whole set with exceptions listed, else inferred.

Matched (re-run and independently recomputed; X = `money` / `total` - 1):
- TUR home / away X: S79 0.75 / 0.85, S80 0.82 / 0.92, U03 1.02 / 1.12, U04 1.07 / 1.17, U05 1.07 / 1.07 (home merchant in U05 only); every away node of a save gives the same X within 0.0003.
- Pairs (one pair per away merchant entry, both totals >= 3): U03 home without merchant +0.10 x 6, with merchant 0.00 x 10; U04 6 / 8; U05 2 / 14; no other value occurs (per country: 3/8, 3/7, 2/8).
- Strict subset (merchant at home, ideas, reforms, diplomatic technology, modifier names unchanged; home X measurable with total >= 3 in both saves): 6 of 22 change in U03 -> U04 (POL -0.25, MAI -0.05, YEM +0.10, TRS +0.05, KON +0.05, KOR -0.025) and 5 of 14 in U04 -> U05 (NUM +0.10, JAP +0.15, DEC -0.10, REG -0.225, BLG +0.10). The response's criteria do not include the number of estates with loyalty >= 60; adding it leaves U03 -> U04 at 22 and reduces U04 -> U05 to 13 countries (still 5 changing).
- Estate-loyalty hypothesis counter-cases: RUS 2 -> 0 estates >= 60, dX 0.0; GEN 1 -> 0, dX 0.0; SND 0 -> 1 and 1 -> 0, dX 0.0 both; not mentioned before and also against the hypothesis: SLZ 1 -> 0, dX -0.075; AJU 0 -> 1, dX +0.25. In favour: only TUR (1 -> 2, +0.05).
- TUR changes U03 -> U04 and U04 -> U05 (modifier keys, `spy_ideas` 0 -> 1, estate 0 loyalty 57.8 -> 66.7, unchanged ideas/reforms/technology/mercantilism 30 in U04 -> U05); S80 -> U03 technology 21/21/22 -> 22/22/23 and `trade_success`, `diplomatic_moves` added.

Corrected:
- YEM gulf_of_aden (U04 -> U05) is not a clean second case: in the same interval two estates crossed loyalty 60 (0 -> 2; 57.4 / 50.5 -> 60.9 / 61.0), and YEM's home X rose by 0.10 in the previous interval too without any merchant change (0.22 S80, 0.32 U03, 0.42 U04, 0.52 U05; YEM is one of the six unexplained U03 -> U04 changes in the strict subset). So YEM's +0.10 cannot be attributed to the home merchant and does not favour M over N.
- "Away collecting merchants exist only in S79 and S80 (99 entries)": U03, U04 and U05 contain 48 away-collecting merchant entries each (S79 49, S80 50; U01/U02 copy S80/S79); the 99 is the S79 + S80 count. The 78 start saves still have none. The new entries are the same campaign and the same countries, not independent data.

Unverifiable here: the trade-efficiency effects of `trade_success`, `discontent_sowed`, `dip_boost` and `old_rights_granted_to_nobility` (not in the save); hence M versus N stays UNKNOWN.

## Update 2026-10-05 - save U06

Status: single runs of `backend/scripts/research/u06_*.py` (`u06_tur_nodes.py`, `u06_series.py`, `u06_steps.py`, `u06_mods.py`, `u06_tur_money.py`, `u06_dx_tech.py`, `u06_dx_level.py`, `u06_step11.py`, `u06_merchants.py`, `u06_stages.py`) plus one independent recomputation of the headline numbers (`u06_indep.py`: trade values through `app.trade.extract.extract_world`, country values by regex on the melted text), which matched. Labels: `confirmed` = whole set with exceptions listed, `inferred` otherwise.

New data: U06 (TUR, in-game date 1696.3.25; stored user case U06, file `U06_TUR.1696.03.25.eu4`) continues the campaign of S79, S80, U03, U04, U05 and is not independent of them. Its previous save is U05 (1693.4.15). The save was delivered as a save with "some tech improvement for trade".

### U-3 What changed for TUR between U05 and U06 (country level)
Changed (and plausibly trade-related):
- Technology: adm 22 -> 23, dip 22 -> 23 (mil 23 unchanged). Earlier steps of the series: S79 19/19/20, S80 21/21/22, U03 22/22/23, U04 22/22/23, U05 22/22/23.
- Parliament: U03-U05 had `enacted_parliament_issue = reduce_trade_regulations` and no active issue; U06 has no enacted issue and `active_parliament_issue = charter_trade_companies` (date 1694.6.22, back 20).
- Merchants: 8 -> 9 (`countries.TUR.merchants.envoy` entries; merchant entries in the trade block 8 -> 9); the new one collects at `venice`.
- Ships protecting trade: 109 -> 154.
Unchanged (checked): `active_idea_groups` (all seven groups, same levels), `government` reforms (same 11 reforms in `reform_stack`), `active_policy` list, the `modifier` list (same 16 keys: `dip_boost`, `diplomatic_moves`, `discontent_sowed`, `house_of_worship`, `india_trade_co`, `khalifah`, `mecca_timer`, `pious_ruler`, `thalassocracy`, `tur_janissary`, ...), mercantilism (30.0), institutions, estate privileges (estate loyalty: church 63.1 -> 58.8, burghers 85.8 -> 86.3).

### U-4 Trade efficiency X = money / total - 1 (updates Q1 and the X series)
| Save | Date | TUR home X | TUR away X | Merchant at home | dip/adm tech |
|---|---|---|---|---|---|
| S79 | 1665.4.22 | 0.75 | 0.85 | no | 19 / 19 |
| S80 | 1682.4.18 | 0.82 | 0.92 | no | 21 / 21 |
| U03 | 1691.1.9 | 1.02 | 1.12 | no | 22 / 22 |
| U04 | 1691.11.1 | 1.07 | 1.17 | no | 22 / 22 |
| U05 | 1693.4.15 | 1.07 | 1.07 | yes | 22 / 22 |
| U06 | 1696.3.25 | **1.12** | **1.12** | yes | 23 / 23 |

- U05 -> U06: X rose by exactly +0.05 at all 5 collecting entries present in both saves (`constantinople` (home), `the_moluccas`, `comorin_cape`, `gujarat`, `gulf_of_aden`: 1.07 -> 1.12), and the new collector `venice` has X = 1.12 as well. Home X equals away X in U05 and U06 (home merchant present); in U03 and U04 (no home merchant) away X = home X + 0.10. Both M and N fit this (confirmed as a description of the 6 TUR points; the pattern is the same as in U-1).
- Size: at the U06 shares (sum of `total` over TUR's collecting entries 122.325) +0.05 is worth 0.05 x 122.325 = 6.12 ducats per month (derived, not recorded).
- TUR trade income (sum of `money` of the collecting entries): U03 252.368, U04 249.244, U05 239.602, U06 259.326 (+19.724); the change contains the new `venice` collector (+21.967) and a lower `constantinople` share (`total` 63.281 -> 54.538, money 130.991 -> 115.620); the per-node pieces are recorded values, their causes are not analysed here.
- Nothing else that the save shows changed between U05 and U06 apart from the tech levels and the parliament issue (and the ship/merchant counts above), so the +0.05 is attributable to {adm and dip tech 22 -> 23, parliament issue, 9th merchant} jointly; the save cannot separate them (inferred).

### U-5 Is there a tech-level -> X mapping? (tested, not found)
`u06_dx_tech.py` / `u06_dx_level.py`: entries collecting in both of two consecutive saves of the series (S79..U06; 5 pairs) at the same node with the same `has_trader` and `has_capital` flags, dX by the change of the country's (adm, dip, mil) tech levels:
- No tech change (0,0,0): 151 entries, dX = 0.00 in 100, the rest scattered (-0.10 x 10, +0.05 x 8, +0.25 x 6, +0.15 x 5, ...): X moves for reasons other than tech in about a third of the entries.
- Single dip step (adm unchanged): 23 -> 24: 14 entries, dX = +0.02 in 9 (others +0.07 x 2, -0.08, +0.10, -0.03); 22 -> 23: 16 entries, dX = 0.0 (3), +0.2 (3), +0.4 (3), +0.3 (2), -0.05 (1) and 4 other values: no modal value; 21 -> 22: 7 entries, dX = 0.0 in 4.
- Single adm step (dip unchanged): 22 -> 23: 16 entries, dX = 0.0 (5), -0.2 (3), -0.15 (2), +0.2 (2), ... no modal value; 23 -> 24: 6 entries, 0.0 in 3.
- U05 -> U06 countries whose adm and dip both rose by 1 and that have a comparable collecting entry: 7. TUR +0.05 (5 nodes, no change of modifiers, ideas, policies or reforms; parliament issue changed), BOH +0.02 (dip 23 -> 24, no change of modifiers, ideas, policies, reforms; parliament issue enacted), DEC -0.10, JAP -0.08, MAG +0.25, MIR +0.30, MLI +0.12 (each with modifier changes).
- Verdict: a per-level tech value is UNKNOWN. What the data supports (inferred): dip 23 -> 24 gives +0.02 in 9 of 14 single-step cases; TUR's +0.05 at 22 -> 23 (adm and dip together) is the only clean case for that step and therefore cannot be split between adm, dip and the parliament issue. The draft's "diplomatic tech +0.02 per level" is not contradicted at 23 -> 24 and is not supported at 22 -> 23 (single dip steps show no modal value there); it remains unsourced.

### U-6 Merchant count and pipeline stages
- 9th merchant: in the other consecutive-save cases with a dip +1 step and unchanged ideas, the merchant count rises in 2 of 12 cases at 22 -> 23 (0 in 10) and in 0 of 7 at 23 -> 24 (`u06_merchants.py`); no general "dip level -> +1 merchant" rule is visible. The source of TUR's 9th merchant is UNKNOWN.
- Stage checks of the project (`u06_stages.py`), failures / checks: propagation 109/973, raw_power 539/890, val 0/879, transfers 0/474, retain_power 0/80, pull_power 0/77, retention 0/80, current_value 0/128, steer_weights 125/159, link_flow 111/159, income_share 0/370, income_efficiency 3/51 (MOR `ivory_coast` 2.691 vs 2.707, MOR `safi` 1.424 vs 1.433, C14 `brazil` 1.095 vs 1.098; no TUR entry); first failing stage `propagation`, chain `unknown_variable`: the same pattern as U03-U05.

### What settles it (U06 adds)
- The trade-efficiency value of dip/adm technology level 23 in 1.37.5 and of the parliament issues `reduce_trade_regulations` (enacted) and `charter_trade_companies` (active): a sourced statement, or a save pair in which only one of them changes.
