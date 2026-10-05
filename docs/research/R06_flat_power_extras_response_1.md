# R06 response 1 - Flat power additions (capital, merchants, placed_merchant_power, modifiers)

Scope: only what the 82 fixture saves settle; all numbers from `backend/scripts/research/r04_r05_r06_r06a.py` (helper `r04_r05_r06_flat.py`; snapshot of the repo in /tmp/eu4research/repo). "extras" = `max_pow - province_power - ship_power - prev` of an entry (85,968 entries with `max_pow`). "Snapshots" = S01-S78; "played" = S79, S80, U01, U02 (saved mid-month, with a played-in country; same mod list as S14, version 1.37.5). Classes: home = `has_capital`; collect-away = `total` key, no capital; steer = `type` key; passive = none of these; "+merchant" = `has_trader`.

## Q1 - Where does the +2 apply?

### C-Q1.1 The extras are capital 5 + node modifiers + a country-level merchant term R; R is 0 in all 78 snapshots
Claim: extras = 5 x `has_capital` + sum(`modifier.power`) + R, where R is zero for every entry of the 78 snapshots (0 exceptions among all snapshot entries) and non-zero only for merchant entries of the four played saves.
Formula: R = 0 (snapshots); R in {2, 7, 17, 22} (played saves, see C-Q1.2).
Applies when: see caveats.
Source: save corpus, `r04_r05_r06_r06a.py`.
Quote (extras by class, all saves): home 5.0: 5,944 of 5,950; home+merchant 5.0: 36,366 of 36,804 (others 7.0 250, 22.0 82, -3.0 40, 12.0 40, 27.0 24, 2.0 2); steer+merchant 0.0: 19,768 of 21,448 (2.0: 902, 17.0: 378, 7.0: 156, 22.0: 144, -8.0: 68, -3.0: 26, 42.0: 4, 12.0: 2); passive 0.0: 16,606 of 16,628; passive+merchant 0.0: 4,831 of 4,940; collect-away+merchant: 198 entries, never 0 (2.0: 80, 17.0: 56, 7.0: 34, 22.0: 22, -8.0: 4, -3.0: 2). After subtracting 5 x capital and the modifier powers, the residual R is 0 in every entry outside the four played saves ("nonzero residual outside played saves: 0").
Confidence: confirmed (whole corpus, 0 exceptions).
Caveats: the hypothesis in the request ("+2 only for a merchant that collects away from the capital, home-node and steering merchants add 0") is contradicted by the played saves: there every class gets R (next claim). It is only true of the 78 snapshots, where R = 0 for every class, including collect-away entries (which exist only in the played saves, 198 entries).

### C-Q1.2 In the played saves every merchant entry gets R = 2 + 5a + 15b, constant per country
Claim: in S79/S80/U01/U02 the merchant term is a country-level constant applied to every entry with a merchant, whatever its action (home, steer, collect-away, passive).
Formula: R = 2 + 5 x [government reform `mercantilistic_approach_reform` or `pious_merchants_reform`] + 15 x [idea group `trade_ideas` level >= 5].
Applies when: the save is one of the played saves and the entry has a merchant (`has_trader`); it does not apply to the snapshots.
Source: save corpus (trade block + `countries` block: `government.reform_stack.reforms`, `active_idea_groups`), `r04_r05_r06_r06a.py`.
Quote: residual per country-save is a single value in 642 of 644 country-saves (7.0 / 17.0 for VER only: wien, saxony, north_sea 7.0, rheinland 17.0); values: 2.0 in 444, 17.0 in 98, 7.0 in 72, 22.0 in 28. In S80, `trade_ideas` level: residual 17.0 -> 23 countries with level 7, 2 with 5, 1 with 6; residual 22.0 -> 6 with 7, 1 with 6; residual 2.0 or 7.0 -> levels 0-4 or no `trade_ideas` (0 exceptions). Feature search (S80, 24 countries with +5 vs 124 without; S79, 26 vs 147): `reform:mercantilistic_approach_reform` 18 of 24 (and 21 of 26) with 0 false positives, `reform:pious_merchants_reform` 5 (and 4) with 0 false positives. Checking the formula per country-save: S79 172 of 173 correct, S80 147 of 149; exceptions: SND (observed 22.0, formula 17.0, +5 from an unidentified source), VER (rheinland 17.0 against 7.0 elsewhere: a node-specific +10 not explained).
Confidence: inferred (fit on two saves, feature search over reforms/privileges/modifiers/ideas; the three constants 2, 5, 15 are fitted sums, their game names are not in the save). The values 2, 5, 15 are consistent with placed/merchant-power country modifiers but no source is given here.
Caveats: in the 78 snapshots the same formula predicts R > 0 for 1,842 country-saves with merchants in the four snapshots checked (S14, S42, S67, S78) (e.g. S42: 86 country-saves with `trade_ideas` >= 5 predict 17, 330 predict 2; S67: 101 / 252; S78: 84 / 327; S14: 662 predict 2) and all observe 0. Why the snapshots lack the term (bookmark-start state versus played game) is UNKNOWN; a start save of a played game, or a played save on the first of a month, would settle it. **Updated 2026-10-05:** the played save U04 is dated the 1st of a month and still has R > 0 (section Update, U-1), so the mid-month explanation is refuted; the difference is start/bookmark state versus played game.

### C-Q1.3 Entries whose `has_trader` key is absent but which carry R
Claim: 4 entries carry R without `has_trader`: S79/U02 TMB at timbuktu (home, extras 7.0 = 5 + 2) and S80/U01 SCA at carribean_trade (passive, `max_pow 17.0` and no other key).
Confidence: observed; the rule for them is UNKNOWN (the merchant exists but the flag is missing).
Line in the draft `or country_entry.has_capital`: contradicted, home entries without a merchant get exactly 5.0 (5,944 of 5,950; the 2 exceptions are TMB above and 4 are -5.0 = 5 - 10 with a recall).

## Q2 - Recalled merchants

### C-Q2.1 The -10 is added on top of the normal terms; `merchant_recalled` power is always -10
Claim: `merchant_recalled` is a node modifier with `power` -10 in all 168 occurrences; `duration` varies from 69 to 3,647 and `power` does not depend on it (no decay visible).
Quote: home+merchant extras -3.0 (40 entries) = 5 + 2 - 10; steer+merchant -8.0 (68) = 2 - 10; steer+merchant -3.0 (26) = 7 - 10; home without merchant -5.0 (4 entries) = 5 - 10 (`has_trader` absent there); passive -10 (2 entries). These fit "5 x capital + modifier + R" with R from C-Q1.2, so the request's "5 - 10 = -5, not -3" is correct only for entries without R: the -3 rows exist because those are played-save entries that carry R = 2.
Confidence: confirmed for the arithmetic (all 168 recalled entries are in the played saves). Why `has_trader` is still set on a recalled merchant: UNKNOWN. Meaning of `duration` units: UNKNOWN. One exception: S80/U01 VER rheinland observed 7.0 where the formula gives -3.0 (recall term not applied there); unexplained.

## Q3 - Decomposition of all unusual rows

### C-Q3.1 Full decomposition, played saves
Claim: extras = 5 x capital + sum(modifier powers) + R(country) x [has_trader] reproduces 3,676 of 3,708 entries (99.1%) of the four played saves; all 78 snapshots are reproduced with R = 0.
Quote of the modifier terms seen in the corpus (key, power: entries by class): `GEN_ITALIAN_MERCHANT_INFLUENCE` +20 (passive+merchant 72, passive 4), `BYZ_colony_in_galata` +20 (passive+merchant 35), `the_muskovy_trade_company` +20 (passive 4), `COTTON_IMPORTS_BANNED` -10 (passive 10, steer+merchant 2, collect-away+merchant 4), `pirate_hunting` -10 (home+merchant 10), `merchant_recalled` -10 (168), `merchants_too_succesful` +5 (steer+merchant 6), `income_bonanza` +25 (steer+merchant 4). So the 107 passive+merchant rows with extras 20.0 are the three +20 modifiers (not a merchant term), and the 42.0 rows are 2 + 15 + 25 (`income_bonanza`), 27.0 = 5 + 22, 12.0 = 5 + 7, 22.0/7.0/17.0 are R values (C-Q1.2).
Exceptions (32 entries): SND (+5 extra at every steering node and gujarat, in S79, S80, U01, U02), VER rheinland (above), TMB and SCA (no `has_trader` key), nothing else. **Updated 2026-10-05:** SND fails in U03, U04 and U05 too, and MKL north_sea is a new node-specific +5 in U05 (section Update, U-1).
Consistency across nodes: the residual is identical in every node of a country in 642 of 644 country-saves (all nodes of C03, C06, TUR, MIR, KON, MOR, POR ... in all four played saves), so one country-level `placed_merchant_power`-type value is consistent with the data; the exceptions are SND/VER.
Confidence: confirmed as a description of the data (counts above); the game names of the terms are UNKNOWN.

## Q6 - Remaining extras values
Covered by C-Q3.1: 42.0 = 2 + 15 + 25 (`income_bonanza`); 22.0 / 27.0 = R 22 without / with capital 5; 2.0 for a passive+merchant entry (2 entries) = R 2. The 2 home+merchant entries with extras 2.0 are S79 and U02 LIT at `kiev` (`has_capital`, `merchant_recalled` -10, no other modifier): 5 + 7 - 10 = 2, with LIT's R = 7 in all its merchant nodes of S79 (kiev, novgorod, baltic_sea); they fit the formula and are not among the 32 exceptions.

## Not answered (needs an outside source)
Q1 "quoted source" for the rule, Q2 duration semantics in the game files, Q4 (file + line for `placed_merchant_power`; whether it applies to steering/passive merchants - the data say it applies to all classes in the played saves), Q5 (`power_modifier` and `TRADE_POWER_HOME_BONUS` quotes; `power_modifier` is 0 in every block of the corpus, which is all the data say).

## Updated UNKNOWN list
- Why R = 0 in the 78 snapshots but non-zero in the played saves (needs a played-game save on a tick day or an intervention pair).
- The game names and sources of the constants 2 (per merchant), 5 (reform), 15 (trade ideas level >= 5).
- SND's extra +5, VER rheinland's node-specific +10 and missing recall term, TMB/SCA entries without `has_trader`.

## Verification (date 2026-10-04)
Independent re-computation in `backend/scripts/research/ver_r06.py` (own loop over the parsed saves in integer thousandths; country data from the cached `countries` block; no author code reused); the author's `r04_r05_r06_r06a.py` was also re-run.

Re-run and matching:
- 85,968 entries with `max_pow`; the by-class extras table (home, home+merchant, steer+merchant, passive, passive+merchant, collect-away+merchant) matches every count quoted in C-Q1.1.
- After subtracting 5 x `has_capital` and the node modifier powers, the residual is non-zero in 0 entries outside the four played saves (0 of 82,260 snapshot entries).
- `merchant_recalled`: 168 occurrences, `power` -10 in all, `duration` 69 to 3,647, all in played saves; other modifier terms and their class counts as listed in C-Q3.1.
- Merchant countries: 42,616 country-saves, 644 with a non-zero residual (all in played saves), 642 single-valued (2.0: 444, 7.0: 72, 17.0: 98, 22.0: 28), the 2 multi-valued are VER in S80 and U01 (7.0 / 17.0). Entries without `has_trader` that carry a residual: S79/U02 TMB `timbuktu` (2.0) and S80/U01 SCA `carribean_trade` (17.0).
- Rule R = 2 + 5 x [`mercantilistic_approach_reform` or `pious_merchants_reform`] + 15 x [`trade_ideas` >= 5]: S79 172 of 173 country-saves, S80 147 of 149 (exceptions SND in both, VER in S80); feature counts S80 18 (mercantilistic) + 5 (pious) of 24 countries with +5, S79 21 + 4 of 26, 0 false positives among 124 / 147 others; the only +5 country without either reform is SND. Entry level: 3,676 of 3,708 played-save entries reproduced.
- Snapshots: the rule predicts R > 0 for 1,842 merchant country-saves of S14, S42, S67, S78 (S14 662 x R=2; S42 330 x 2, 86 x 17; S67 252 x 2, 101 x 17; S78 327 x 2, 84 x 17) and all observe 0.

Corrected: Q6 "2 home+merchant entries with extras 2.0 ... UNKNOWN" is resolved (S79/U02 LIT at kiev, 5 + 7 - 10); the request_2 open-item row for it was removed and the fact added.

Not verified / note: C-Q1.2 and Q1.3 wording about VER rheinland is the same fact seen two ways (residual 17.0 against 7.0 at its other nodes = observed extras 7.0 where R + recall gives -3.0); the game names and sources of 2, 5, 15 remain UNKNOWN; the rule is a fit on one played game (four files, two distinct saves), so `inferred` is the right label.

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below come from one run each of the scripts `backend/scripts/research/u345_home_*.py` (and `u345_ships_*.py` where stated). Unlike the Verification section above they have not been re-computed by an independent verifier. Labels: `confirmed` = whole set with exceptions listed, `inferred` = otherwise.

New data: U03 (1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign as S79 (1665.4.22) and S80 (1682.4.18). They are not independent of S79/S80 or of each other.

### U-1 The merchant term R on three more saves
Formula under test (unchanged): extras = 5 x `has_capital` + sum(`modifier.power`) + R, R = 2 + 5 x [`mercantilistic_approach_reform` or `pious_merchants_reform`] + 15 x [`trade_ideas` >= 5], for countries with a merchant.
- Merchant countries that fit the formula: S79 172 / 173, S80 147 / 149, **U03 136 / 137, U04 136 / 137, U05 132 / 134**. SND fails in every new save (observed R = 22, formula 17: the +5 of Q3 continues). U05 adds **MKL**: R = 2 at saxony and rheinland but 7.0 at north_sea only in U05 (it was 2.0 at all three nodes in U04; no modifier listed) [corrected in the second-pass verification below: MKL has four merchant nodes] - a node-specific +5 like VER rheinland in S80 [VER's extra is +10, not +5: see the second-pass verification below].
- Entries without `has_trader` that carry R: 0 in U03, U04 and U05 (the TMB and SCA cases of C-Q1.3 are not repeated).
- **U04 is dated the 1st (1691.11.1), a tick day.** R is non-zero there like in the mid-month saves (U03 1691.1.9, U05 1693.4.15, S79, S80). So "R > 0 only because the played saves are written mid-month" is refuted: R > 0 goes with a played game (all 78 start snapshots have R = 0). Confidence: confirmed for "not a mid-month effect" (136 of 137 merchant countries of a tick-day save have R as predicted). Why start snapshots lack R stays UNKNOWN.
- TUR: R = 17 at every merchant entry of all five saves (S79, S80, U03, U04, U05). In U05 constantinople (home, collecting, with a merchant for the first time) has extras 22.0 = 5 (capital) + 17; in U04, with no merchant there, 5.0. So a home merchant that collects gets R like any other merchant entry; TUR's ideas and reforms do not change across the five saves, so no change of R was expected or seen.
- Cross-check from the ship analysis (`u345_ships_maxpow.py`): for entries with ships, `max_pow - province_power - ship_power - prev - 5 x has_capital - sum(modifier.power)` equals the country's constant R (taken from its ship-less entries) within 0.0025 in 476 of 476 entries (S79 92, S80 90, U03 94, U04 100, U05 100), with coefficient 1 on `ship_power`.

### Verification 2026-10-05 (second pass)

Independent code (new, not reusing the author's logic): `backend/scripts/research/ver2_b_lib.py`, `ver2_b_tur.py`, `ver2_b_bonus.py`, `ver2_b_resid.py`, `ver2_b_x.py`, `ver2_b_switch.py`, `ver2_b_corpus.py`; corpus of 85 saves (S01-S80, U01-U05; U01/U02 copy S80/S79). Each Update claim was re-run and recomputed. Labels follow the rule confirmed = whole set with exceptions listed, else inferred.

Matched (re-run and independently recomputed; residual = `max_pow - province_power - ship_power - prev - 5 x has_capital - sum(modifier.power)` of entries that have `max_pow`; formula R = 2 + 5 x [mercantilistic_approach_reform or pious_merchants_reform] + 15 x [trade_ideas >= 5]):
- Merchant countries / formula fits: S79 173 / 172, S80 149 / 147, U03 137 / 136, U04 137 / 136, U05 134 / 132 (U01/U02 copy S80/S79); exceptions SND (22.0 against 17 in every new save: malacca, ganges_delta, doab, lahore, deccan, comorin_cape), MKL (U05), VER (S80, as before).
- Entries without `has_trader` whose residual is not 0: 0 in U03, U04, U05 (TMB in S79 and SCA in S80 as before). All 61,072 merchant entries of the 78 snapshots have residual 0.
- TUR: residual 17.0 at all 8 merchant entries in each of the seven played-save files; constantinople extras 5.0 in U04 and 22.0 in U05 (5 + 17).
- U04 is dated the 1st and has R > 0.

Corrected:
- MKL has four merchant nodes (lubeck, north_sea, rheinland, saxony), not three: in U04 all four have R = 2.0; in U05 lubeck, rheinland and saxony are 2.0 and north_sea is 7.0.
- "a node-specific +5 like VER rheinland in S80": VER's deviation at rheinland is +10 (17.0 against 7.0 at its other nodes), MKL's at north_sea is +5; both are node-specific, the sizes differ.

Unverifiable here: the cross-check "476 of 476 entries with ships" belongs to the ship analysis and is verified in R11; the three constants' origin.
