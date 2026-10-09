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

## Update 2026-10-05 - Venice series U07-U30 (controlled game)

Data: the Venice series U07-U30 (player VEN, game 1.37.5, non-Ironman plain-text saves, same mod list as S01, new campaign started 1444.11.11): U07 1444.11.11, U08 11.14, U09 11.30, U10 12.01, U11 12.02, U12 12.11, U13 12.31, U14 1445.01.01, U15 01.02, U16 01.15, U17 01.24, U18 01.30, U19 01.31, U20 02.01, U21 02.03, U22 02.10, U23 02.17, U24 02.28, U25 03.01 (U07-U25: no player action at all); then U26 03.31 (all three VEN merchants recalled during March), U27 04.01, U28 05.01 (ragusa merchant sent again), U29 06.01 (alexandria), U30 07.02 (wien). Scripts: `backend/scripts/research/venice_a_*.py` (loader `venice_load.py`), second pass `venice_a_ver.py` (raw text diff of the `trade` block, own Decimal loop for `prev`).

### V-R06-1 The merchant term R is 0 until the first 1st of the game and then 2 per merchant entry
Claim: residual R = `max_pow - province_power - ship_power - prev - 5 x has_capital` (entries without node modifier) is 0 for every entry in U07, U08, U09 (1444.11.11 - 11.30) and from U10 (1444.12.1) on equals the country value for every entry with `has_trader` and 0 for entries without. So "R = 0 in the start snapshots" (C-Q1.1) is the state before the first monthly computation, not a property of start versus played games.
Source: `venice_r06.py` (per-save table) and `venice_a_r06.py`.
Quote (merchant entries by R): U07 843 x 0.0; U08 784 x 0.0; U09 774 x 0.0; U10 988 x 2.0 and 5 x 7.0, no-merchant entries 409 x 0.0 and 7 x 2.0; U14 (1.1) 1,044 x 2.0 and 7 x 7.0, no-merchant 444 x 0.0; U20 (2.1) 1,049 / 7, 443 x 0.0; U25 (3.1) 1,051 / 7, 438 x 0.0; U27 (4.1) 1,047 / 7, 442 x 0.0; U30 1,051 / 7, 439 x 0.0.
Confidence: confirmed.

### V-R06-2 Between 1sts the extras stay at the last 1st value, whatever the merchant does
Claim: an entry whose merchant arrived after the last 1st has R = 0 until the next 1st (all 2 / 8 / 11 / 4 such entries in U11 / U12 / U13 / U16 had no `has_trader` at the preceding 1st); an entry whose merchant left keeps R until the next 1st (U12: 23 of 30, U13: 41 of 48, U26: 4 of 4 had `has_trader` at the preceding 1st). The other 7 of the no-merchant entries with R = 2 already appear in U10 itself: they had `has_trader` in U09 (11.30; `gujarat` NGA, `persia` SIS, `wien` LBV, `saxony` ANH and BRU, `rheinland` WBG and TTL) and had lost it by the save of the first 1st while still carrying R = 2, so the computation of the 1st saw the merchants that the flags of the same save no longer show (order inside the 1st: inferred).
Quote: U11 (12.02) 2 merchant entries with R = 0, U12 (12.11) 8, U13 (12.31) 11, U16 (1.15) 4 (all become 2.0 at U14/U20); no-merchant entries with R = 2.0: U10 7, U11 14, U12 30, U13 48, U26 (03.31, VEN's three recalled merchants plus one) 4; all 0 again on the next 1st (U14 0, U27 0).
Confidence: confirmed. This is the probable explanation of the 4 entries with R but no `has_trader` (TMB `timbuktu`, SCA `carribean_trade`; both saves were taken mid-month): inferred, those entries were not followed across a tick.

### V-R06-3 `merchant_recalled`: duration in days, 3,650 at creation, effect on `max_pow` at the next 1st
Claim: the node-entry modifier `merchant_recalled` (`power` -10) is created with `duration` 3650 and loses 1 per day; it is visible at once but its -10 enters `max_pow` at the next 1st; the entry keeps `has_trader`.
Source: `venice_a_r06b.py` (arrivals / departures) and a listing of the node-entry modifiers of U07-U30 (`modifier` keys with `power`, `duration`); the residual per entry as in `venice_a_r06.py`.
Quote: HED `ethiopia`: modifier first seen in U09 (11.30) with duration 3637, 3636 at U10 (12.01), 3635 at U11 (12.02), 3626 at U12 (12.11) (if the countdown is 1 per day from 3650 the modifier was created on about 11.17); NJR `ethiopia` 3644 at 11.30 (about 11.24); TRE `astrakhan` 3650 at U12 (12.11). Residuals: HED 0.0 at 11.30 (NJR has no `max_pow` yet), both -8.0 (= 2 - 10) at 12.01 and later; TRE 2.0 at 12.11 and 12.31, -8.0 at 1.1. All three entries keep `has_trader` to U30 (duration 3,423 / 3,430 / 3,447 at 07.02).
Confidence: confirmed for the rows; the end of the modifier is not reached (10 years).
VEN's own recall of three merchants (U26) and re-sending (U28-U30) created no `merchant_recalled` modifier at all: UNKNOWN why (AI recall versus player recall, or the circumstances of the recall).

### V-R06-4 A third +5 reform
Claim: R = 2 + 5 x [reform in {`mercantilistic_approach_reform`, `pious_merchants_reform`, `arabic_plutocracy_reform`}]: of 663 countries with merchants in U10, R = 7 for exactly two, Ormuz and Oman, both with `arabic_plutocracy_reform`, and R = 2 for the other 661 (0 exceptions in U10-U30). `venice_merchants_reform` (VEN) gives 2. The +15 term (`trade_ideas` level >= 5) is not testable in 1444-1445 (no country has it).
Source: `venice_a_r06.py`. Confidence: confirmed as an association (2 countries).

### Not settled
Game names and values of 2, 5, 15; SND/MKL/VER/TMB/SCA cases of the TUR campaign (except V-R06-2); the request_2 rows below.

### Verification 2026-10-05 (second pass)
V-R06-1/2 use a second implementation: residual re-derived from the raw text diff counts of `max_pow` / `prev` / `province_power` lines (`venice_a_ver.py 1`: no `max_pow` line changes between 1sts, lines of `max_pow` change on the 1sts only) and `venice_r06.py` (own loop) versus `venice_a_r06.py` (country-level formula).

## Data basis (2026-10-06)

On 2026-10-06 the research data was rebuilt (`docs/research/data_audit.md`): only **clean** saves are kept (the 1st of a month after the game's first trade computation, none of the player's merchants or fleets on the way; R12 final). Kept: U04 (TUR 1691.11.01), U10, U14, U20, U25, U27, U28, U29 (VEN 1444-1445). Removed: the 78 start snapshots S01-S78 and U07-U09 (saved before the first computation: steering weights, `add` and other computed fields are placeholders there) and 21 mid-month saves (S79, S80, U01-U03, U05, U06, U11-U13, U15-U19, U21-U24, U26, U30: numbers from the last 1st, merchant/ship flags from the save day). Counts above that include removed saves are kept as recorded but are **unverified on clean data** unless listed as re-checked below. Clean-data stage results quoted here: `scripts/verify_all.sh` on the 8 kept saves (calc 0.2.0).

- "R = 0 in all 78 start snapshots" is a **pre-first-tick artifact**: `max_pow` incl. the merchant term is recomputed only on the 1st (R12 final). The per-country merchant power R is integrated as an observed input; on clean data `raw_power` fails 7 of 11,307 checks (1 of 8 saves).
- The formula R = 2 + 5a + 15b was fitted on S79/S80 (mid-month, removed): unverified on clean data.


## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R06-1 Node power modifier and merchant terms
Claim (E14): a node modifier `{key=exp_trade_power power=10}` on VEN at ragusa adds 10.000 to `max_pow` (1:1), `val` +10.360, no change of `province_power` or upstream `prev`. Claim (P04): a newly placed fourth VEN merchant steering at constantinople carries the merchant term R = 2 (`max_pow` +2.000) at the first tick. Claim (P03): a merchant switched from steering to collecting away keeps its term (`max_pow` unchanged at ragusa) - this answers whether collecting-away merchants carry the term after the first 1st. Confidence: confirmed.

### V2-R06-2 The +15 term and the trade idea group
Claim (E22): completing `trade_ideas` (all 7 ideas, console `add_idea_group trade_ideas VEN`) adds +15.000 to `max_pow` at each node where VEN has a merchant (ragusa, venice, wien) at t1; `max_demand` +0.200 everywhere; `add` 0.071 -> 0.083. So a +15 merchant-node term is carried by the trade idea group (which idea is not separated: the command grants all seven). Confidence: confirmed for the group; the single idea is inferred-open.

## Update 2026-10-08 - experiment round 2

Source: 27 single-change jobs run in the game by the automation (`tools/EU4-game-automation/experiments/round2/`: `PLAN.md`, `RESULTS.md`, scripts `analysis/`); saves under `round2/out/<id>/` (t1 = 1445.1.1, t2 = 1445.2.1; all dated, player and plain text checked). Controls as in round 1 (E01c / E01d on the E00 base) plus R2-C-U10, R2-H-MAM-C, R2-H-TUR-C, R2-C-NED18. **Void:** every merchant recall by save patch (R2-B5a, R2-B4, R2-B5c, R2-H-MAM-B1, R2-H-TUR-B1 and the recall half of R2-B5b / R2-H-MAM-B2): the patched save has no merchant at the node, t1 has it again (cause unknown); the embargo (R2-EMB) and privateer (R2-PRIV) patches are dropped on load; R2-TC added nothing (no territory province). No claim below rests on a recall.

### V4-R06-1 Capital power +5 moves with the main trade port; merchant at home +2
Claim: R2-PORT `max_pow` +5.000 at the new home node (TRADE_CAPITAL_POWER); R2-B5b / R2-H-MAM-B2: a merchant collecting at home adds +2.000 `max_pow` (venice 110.681 -> 112.681, alexandria 110.564 -> 112.564). Open: -5.000 more at the old home node after the port move. Confidence: confirmed.
