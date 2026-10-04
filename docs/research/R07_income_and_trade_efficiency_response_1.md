# R07 response 1 - Income formula, merchant-present bonus, trade efficiency

Only data-settled points. Scripts: `backend/scripts/research/r07_r08_r12_income.py`, `income2.py`, `x1444.py`. X = money/total - 1 is computed with an interval (money and total are 3-decimal truncated): X in `[money/(total+0.001) - 1, (money+0.001)/total - 1]`.

Corpus limit (important): the 78 start snapshots contain **only home-node collectors** (36,366 entries with merchant + 5,742 without; 0 collecting entries away from the capital). Away collecting merchants exist only in S79 and S80 (99 entries; U01/U02 are the same data), so every away/home test rests on two played saves.

## Q1 - Merchant-present rule
Claim C-01 (confirmed as data): pairs (same country, same save, home X vs away X with `has_trader`, both totals >= 3): home node without merchant: 16 of 16 pairs give away - home = +0.10 (interval contains 0.10); home node with merchant: 28 of 28 pairs give 0.00. (Verification: U01/U02 duplicate S80/S79, so these are 8 and 14 distinct pairs; home without merchant = HAB, TUR, BRI; home with merchant = BRI, CSH, DEC, GEN, GZI, PAP, SPA.) Source: S79, S80 (`income.py`). Quote: TUR S79 constantinople money 123.313 total 70.465 (no merchant) vs ragusa 4.371/2.363 and venice 20.729/11.205 (merchant); S79 GEN home genua `has_trader` X 0.82 vs champagne 0.82 and venice 0.82; S79 PAP home venice (no merchant) 0.87 vs genua 0.969.
Rules compared on all 198 away entries (99 distinct, U01/U02 being copies; the counts below are the 198-entry counts, halve them for distinct entries) with a collecting home entry (X of the country taken from the home entry, bonus 0.10 where the rule says so; `income2.py`): M "+0.10 whenever `has_trader` (any node, home included)" fits 134/134 (home merchant) and 64/64 (home without merchant); N "+0.10 only when away, with merchant, and the home node has no merchant" fits 134/134 and 64/64; A "+0.10 whenever away with merchant" fits 64/64 but fails 134/134 of the home-merchant group; Z "never" fails 64/64. M and N cannot be told apart by pairs. The project's `rule_merchant_bonus(has_trader)` is M and is not contradicted by any pair; the goal's reading that M is refuted by the cross-section is not proven, because that compares different countries.
Cross-section (home entries with total >= 0.4, median X): start snapshots: merchant vs none S01 0.069 vs 0.070, S36 0.089 vs 0.090, S37 0.159 vs 0.180, S38 0.249 vs 0.250, S42 0.269 vs 0.290, S78 0.269 vs 0.270 (no shift of 0.10 at home); played saves: S79 0.45 vs 0.37, S80 0.52 vs 0.419 (shift 0.08-0.10, confounded by country size). So: start snapshots favour "no home bonus" (N), played saves favour M; UNKNOWN. What settles it: one country with a merchant at home whose merchant is recalled (or added) with everything else unchanged (intervention pair), reading X at home before/after.
Rejected: the draft's rule as stated (+0.10 at home for every `has_trader`) is not refuted by the pairs; its 1444 explanation (see Q4) is not supported.

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
