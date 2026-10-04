# R02 response 1 - Away-collection penalty (data-based points only)

Method: all claims come from the 82 fixture saves (S01-S80, U01, U02) and the scripts in `backend/scripts/research/`: `r02_away.py`, `r02_table_rows.py`, `r02_s79_rows.py`, `r02_steer_not_halved.py`, `r02_capital.py` (helpers `common.py`, `r01_r02_r10_build.py`, `r01_classes2.py`). Definitions used: *away* = entry with key `total` and no `has_capital`; *class* = domestic if the node is the node of `country.trade_port` or `top_provinces[0]` is the tag, else foreign; *cap_class* = the country's own `max_demand` at nodes of the same class without merchant/collection and (for embargoed countries) without any embargoer having own power (own = `max_pow - prev`). The goal's table is entirely from S79 (verified: all 30 rows searched were found in S79).

## Q1 - The rows below 0.5

### C-01 The baseline in the goal table was wrong, not the penalty
Claim: against the right same-class baseline every away-collecting row of a country that has no embargoer with power at the node is exactly 0.5 x cap_class. The ratios 0.384 (DEC), 0.597 (DLH lahore), 0.553/0.551 (CSH), 0.538 (MNG), 0.505 (SPA genua) come from a median taken over foreign-class and embargo-reduced nodes.
Formula: `max_demand(away) = 0.5 * cap_class`
Applies when: entry has `total`, no `has_capital`.
Source: save corpus; `r02_away.py`, `r02_s79_rows.py`.
Quote (S79, md / cap_class, from the script output): `DEC comorin_cape dom md=0.720 cap=1.440 -> 0.500`; `DLH lahore dom md=0.821 cap=1.642 -> 0.500`; `DLH gujarat for md=0.688 cap=1.376 -> 0.500`; `MNG ganges_delta for md=0.785 cap=1.570 -> 0.500`; `SPA genua for md=1.069 cap=2.137 -> 0.500`; `CSH yumen for md=0.653 cap=1.306 -> 0.500`; `GZI zanzibar dom md=0.639 cap=1.278 -> 0.500`.
Corpus count: 108 of 108 away-collecting entries of non-embargoed countries that have a single same-class baseline have ratio 0.500 (quantiles min/p10/median/p90/max = 0.5/0.5/0.5/0.5004/0.5007); 2 further entries have no baseline. In S79: 34 of 49 away rows are exactly 0.5 (the first version said 50; the script lists 49).
Confidence: confirmed (corpus-wide, no exception among non-embargoed countries).
Caveats: 0.5 is the whole factor; no row shows `0.5 + r` with r > 0 (the five "above 0.5" rows are 0.500 against their class cap). So `reduced_trade_penalty_on_non_main_tradenode` is 0 for every country that could be tested, but a non-zero r in a country with no clean baseline cannot be excluded (CSH beijing has none: domestic class, md 0.656, only embargoer MNG with own power 2.3).

### C-02 The rows below 0.5 are embargo (per target, not per node)
Claim: every S79 away row with ratio < 0.5 belongs to a country with `trade_embargoed_by` whose embargoer has own power at the node; the ratio is `0.5 * (1 - reduction)`.
Source: `r02_s79_rows.py` (S79).
Quote (md/cap_class; embargoers' own power): GEN champagne 0.465 {SWI 39.2, PAP 26.2, LAN 2.0}; GEN venice 0.450 {PAP 58.8, LAN 39.8}; KON ivory_coast 0.366 {MOR 99.0}; SON ivory_coast 0.366 {MOR 99.0}; MAL ivory_coast 0.458 {KON 54.2}; MOR ivory_coast 0.444 {KON 54.2, SON 19.1}; LAN venice 0.433 {GEN 69.1, PAP 58.8}; PAP genua 0.343 {GEN 265.2, LAN 138.1}; SWI genua 0.396 {GEN 265.2}; RUS baltic_sea 0.445 {DAN 75.6}; SPA english_channel 0.328 {GBR 480.7}; SUN malacca 0.451 {BEI 108.1}; TUR ragusa 0.402 {HUN 13.8, HAB 89.8}; TUR venice 0.485 {HAB 31.5}.
Counter-check (same script): HAB english_channel (embargoed by 2, none has power there) = 0.500; MNG ganges_delta (embargoed by 3, none has power) = 0.500; SPA genua (embargoer GBR has no power) = 0.500; LIT baltic_sea 0.500 while RUS at the same node is 0.445.
Node view: ivory_coast has four countries below 0.5 that are mutually embargoed (KON by MOR; SON by MOR; MAL by KON; MOR by KON+SON); baltic_sea: LIT 0.500 (not embargoed) and RUS 0.445 (embargoed by DAN); english_channel: BRI/HAI/HAB 0.500, SPA 0.328 (embargoer GBR 480.7 own power). This fits a per-target embargo and not a node-level effect.
Magnitude: with the forum formula `0.5 * own_e/(sum own + 5*NH)` (own = max_pow - prev) 4 of 14 rows agree within 1 pp of reduction (GEN champagne, MAL, MOR, TUR venice); the others are off by +1.5 to +13.1 pp (worst: KON/SON ivory_coast +13.1, SPA english_channel +10.0, PAP genua +7.8). So embargo is confirmed as the cause by presence/absence, but its exact magnitude is NOT reproduced (see R01 response, Q1).
Confidence: confirmed for cause (presence/absence, see R01 C-05 for the corpus-wide version), UNKNOWN for exact size.

## Q2 - Steering and non-collecting power

### C-03 Steering and merchants without an action are not halved
Claim: only collecting away halves `max_demand`. Steering away and a merchant without recorded action keep the full class cap.
Source: `r02_steer_not_halved.py`; non-embargoed countries only; ratio md / cap_class, cap_class from passive no-merchant nodes of the same class.
Quote (counts): steer-away (`type` present, no `has_capital`, no `total`): 20,573 of 20,591 entries equal to cap (99.91%); 0 at 0.5. Merchant with `has_trader` but no `type` and no `total`: 4,433 of 4,433 equal to cap. Collect-away: 100 of 102 at 0.5 (the 102 are the away entries that have a passive, merchant-free same-class entry as baseline; C-01 counts 110 away entries, of which 108 have a single same-class baseline from any non-away entry, and all 108 are at 0.5; the 2 exceptions below are SUN malacca in S80/U01: 0.648 vs cap 1.492, ratio 0.434; SUN is embargoed in S79 by BEI, in S80 `trade_embargoed_by` was not listed for SUN, so this is an unexplained exception). Steer-away exceptions: 18 (SUN and DLI in S80/U01, md 1.39-1.49 vs 1.492, i.e. small reductions, not 0.5).
Rows named in the request: GEN saxony (steer) 1.853 and rheinland (steer) 1.845 vs cap 1.907 are reductions of 2.8% / 3.25% explained by PAP (own 22.0) and SWI (2.0 / 16.6); they are not 0.5; TUR gulf_of_aden (steer) 2.110 = cap.
Confidence: confirmed (corpus-wide).
Caveats: the statement is about the saved `max_demand`; it says nothing about province/ship power.

## Q3 - Rows above 0.5
See C-01: all five rows are exactly 0.5 x their class cap. DLH lahore is a domestic-class node (`top_provinces[0]` = DLH) whose cap (1.642) is higher than DLH's foreign cap (1.376); MNG/SPA/CSH baselines in the goal table were lowered by embargo-reduced nodes in the median. Hypothesis (a) `0.5 + r` is not needed anywhere; hypothesis (b) "domestic cap differs from foreign cap" explains DLH, DEC, GZI exactly. The additive-vs-multiplicative form of r cannot be tested (r = 0 in all testable rows): UNKNOWN.

## Q4 - Capital / colonial nations (data part only)

### C-04 `has_capital` marks the node of `trade_port`
Claim: in the corpus the node entry with `has_capital` is the node containing the province `country.trade_port`.
Source: `r02_capital.py` (all 82 saves, provinces block `trade=` of the province).
Quote: 42,754 of 42,754 countries that have a `has_capital` entry have it exactly at the node of `trade_port`; 37,441 countries have no `has_capital` entry (their home-node entry is a bare `max_demand`). In none of the 80,195 country-saves compared is node(`capital`) different from node(`trade_port`) (verification over all 113,160 country-saves that have a `trade_port`: 0 differ; 70,406 of them have no `has_capital` entry), so the corpus cannot say which of the two `has_capital` follows when they differ (Wealth of Nations): UNKNOWN; an intervention save with a moved main trade port is needed (R14).
Confidence: confirmed for the equality, UNKNOWN for the differing case.

### C-05 Colonial nations
Claim: colonial nations (tags C00-C17 in these saves) collecting outside the node of their `trade_port` are halved like any other country (C02, C03, C04, C06, C07, C11, C14, C17 in S79: all 0.500 of their class cap). 486 colonial-nation country-saves do have a `has_capital` entry (so they have a home node) and 87 do not.
Source: `r02_s79_rows.py`, `r02_capital.py`.
Confidence: confirmed for "halved when away"; the case "colonial nation without any home node entry" is not separable from the data: UNKNOWN.
Caveat: the condition that would falsify the reading (a colonial nation collecting at its own `trade_port` node and still halved) does not occur in the corpus: no away-classified row is at the `trade_port` node by construction.

## Q5 - Home bonus (data part only)
See the R01 response, C-04: a home bonus of +0.1 per steering merchant is visible inside `max_demand` at the home node, additive, only in the 4 ticked/played saves, and absent when a merchant collects away (12 of 12).

## Not answered (needs an outside source)
- Q2 bullet 1 (quote for C-02 wiki text, `inferred` wording), Q3 wiki sentence `add onto the -50% base penalty`, Q4 save-field source (pdx-tools/eu4save/rakaly) for the main trade city, Q5 `TRADE_POWER_HOME_BONUS` define line and value, wiki section/banner names for C-05/C-06.
- Source of the value of `reduced_trade_penalty_on_non_main_tradenode` per country (not in the save).

## Still UNKNOWN and what settles it
1. Exact size of the embargo reduction (see R01): needs embargoers' `embargo_efficiency` and caravan power (not in the save), or an embargo on/off pair (R14).
2. r in `0.5 + r` for a country that has it: a save of a country with a known reduction source.
3. Whether `has_capital` follows the capital or the main trade port when they differ: intervention save moving only the main trade port.

## Verification (date 2026-10-04)
Independent recomputations: `ver_r02_away.py` (class caps from passive entries only), `ver_r02_capital.py`; re-runs of `r02_away.py`, `r02_steer_not_halved.py`, `r02_capital.py`, `r02_s79_rows.py`.
- Re-run and matching: 108 of 108 away entries with a single same-class baseline at ratio 0.5 (quantiles 0.5 / 0.5 / 0.5 / 0.5004 / 0.5007); steer-away 20,573 of 20,591 at the class cap and 18 others (SUN and DLI, S80/U01); merchant-without-action 4,433 of 4,433; collect-away 100 of 102 at 0.5, the 2 others being SUN malacca S80/U01 (0.648 vs 1.492); every per-row S79 value of C-01 and C-02 (34 rows at 0.5, 4 embargo-consistent within 1 pp, 10 with the quoted deviations +1.5 ... +13.1 pp, CSH beijing without a clean baseline); `has_capital` at the node of `trade_port` in 42,754 of 42,754 countries that have the entry; colonial nations 486 with / 87 without a `has_capital` entry; GEN saxony 2.83 % and rheinland 3.25 % reductions.
- Corrected: "34 of 50 away rows" in S79 -> 34 of 49 (49 away entries exist in S79); the two collect-away totals (108 of 108 in C-01, 100 of 102 in C-03) are now explained as different baseline definitions; C-04: the independent run over every country with a `trade_port` (113,160 country-saves) finds 42,754 with a `has_capital` entry, all at node(`trade_port`) = node(`capital`) (also 0 countries with node(`capital`) != node(`trade_port`)), and 70,406 without the entry (the first version's 37,441 / 80,195 counted a narrower set of country-saves; the equality result is the same).
- Not verified: the identity of the "2 further entries with no baseline" of C-01 with the SUN malacca pair (the independent run finds the same two as outliers but with a different baseline definition); the C-05 statement that colonial nations C02, C03, C04, C06, C07, C11, C14, C17 are all at 0.500 is confirmed only for the rows listed by `r02_s79_rows.py`.
