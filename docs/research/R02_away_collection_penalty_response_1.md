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
Confidence: confirmed (corpus-wide, no exception among non-embargoed countries). **Updated 2026-10-05:** a within-country switch (TUR gulf_of_aden, steering -> collecting away) shows the 0.5 factor directly (section Update, U-1).
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
Confidence: confirmed (corpus-wide). **Updated 2026-10-05:** the same switch gives a within-country check that steering keeps the full value (gulf_of_aden 1.932 / 1.925 while steering, section Update, U-1).
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

## Update 2026-10-05 - saves U03, U04, U05

Status: the results below come from one run each of the scripts `backend/scripts/research/u345_home_*.py` (and `u345_ships_*.py` where stated). Unlike the Verification section above they have not been re-computed by an independent verifier. Labels: `confirmed` = whole set with exceptions listed, `inferred` = otherwise.

New data: U03 (1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign as S79 (1665.4.22) and S80 (1682.4.18). They are not independent of S79/S80 or of each other.

### U-1 A within-country switch: steering -> collecting away (supports C-01, C-03)
- TUR's actions: home node constantinople (`trade_port 151`, `has_capital`), 8 merchants in the trade entries of every save. U03 and U04: 4 steering (gulf_of_aden, basra, alexandria, crimea), collecting away at the_moluccas, comorin_cape, gujarat, venice. U05: 3 steering (basra, alexandria, crimea), collecting away at the_moluccas, comorin_cape, gujarat and **gulf_of_aden (steering in U04)**. This is the first save pair in the corpus in which the same country switches one node from steering to collecting away. [corrected in the second-pass verification below: S79 -> S80 also has TUR comorin_cape steering -> collecting away, and 24 switches in total]
- `max_demand` of TUR at gulf_of_aden: 1.932 (U03, steering), 1.925 (U04, steering), 1.145 (U05, collecting away). Control node crimea (steering throughout; same class, foreign; no embargoer of TUR has own power at either node in U03-U05): 1.932, 1.925, 2.289. Ratio gulf_of_aden / crimea = 1.0000, 1.0000, **0.5002**. The node that switched is halved relative to its control node and the control is not.
- Confidence: `inferred`: one country, one node pair. The control's own +19% jump between U04 and U05 (1.925 -> 2.289) is unexplained (TUR's modifiers `trade_success`, `discontent_sowed`, `dip_boost` changed in that interval; see R01 response, Update U-2); before the switch gulf_of_aden equals crimea only in U03 and U04, not in S80 (1.596 / 1.263), so the ratio of 1.0000 is not a general identity.
- The home-node question (Q4) is unchanged: TUR's capital and trade port are in the same node in all five saves, so the pair still cannot tell which one `has_capital` follows. In U05 constantinople (home) holds a merchant for the first time (`has_trader`, `total`, `has_capital`); the away factor applies only to entries without `has_capital`.

### Verification 2026-10-05 (second pass)

Independent code (new, not reusing the author's logic): `backend/scripts/research/ver2_b_lib.py`, `ver2_b_tur.py`, `ver2_b_bonus.py`, `ver2_b_resid.py`, `ver2_b_x.py`, `ver2_b_switch.py`, `ver2_b_corpus.py`; corpus of 85 saves (S01-S80, U01-U05; U01/U02 copy S80/S79). Each Update claim was re-run and recomputed. Labels follow the rule confirmed = whole set with exceptions listed, else inferred.

Matched (re-run and independently recomputed):
- TUR's actions per node (U03/U04: 4 steering, away at the_moluccas, comorin_cape, gujarat, venice; U05: 3 steering, away at the_moluccas, comorin_cape, gujarat, gulf_of_aden; constantinople has `has_trader` in U05 only; 8 merchants in every save).
- gulf_of_aden `max_demand` 1.932 / 1.925 / 1.145 against crimea 1.932 / 1.925 / 2.289 (ratios 1.0000 / 1.0000 / 0.5002); no embargoer of TUR has own power at either node in U03-U05; crimea +18.9% U04 -> U05; TUR ideas, reforms, technology, mercantilism and loyalty tiers unchanged in that interval, three modifier keys changed.
- The away rows of the earlier claims on all 85 saves (entries that are away collectors, embargo-clean at the node, with one same-class passive baseline): 214 of 216 within 0.0015 of 0.5 x baseline (122 of 124 in the 82 earlier saves, 92 of 92 in U03-U05); the two exceptions are SUN malacca in S80/U01 (0.648 vs 1.492, ratio 0.434), the same as C-03. (This definition is wider than the response's "108 of 108": it also uses embargo-clean nodes of embargoed countries.) `has_capital` entry at the node of `trade_port`: 42,754 of 42,754 (82 earlier saves) and 411 of 411 (U03-U05).

Corrected / added:
- U-1 "first save pair ... steering to collecting away": not the first. S79 -> S80 contains TUR comorin_cape steering -> collecting away (1.53 -> 0.567, 0.490 x the country's control ratio), 17 years apart and with other changes. What is new in U04 -> U05 is a one-interval pair with a tight control (the foreign scalar is identical at the 36 embargo-clean foreign nodes).
- Added evidence, stronger than the single pair (independent script `ver2_b_switch.py`; S79 -> S80, S80 -> U03, U03 -> U04, U04 -> U05; normalized ratio = (md_B / md_A) / median change of the country's unchanged non-away nodes): 12 nodes where a country starts collecting away and 12 where it stops. Starting: 9 of 12 give 0.489-0.514 (TUR gulf_of_aden 0.5002, RUS baltic_sea 0.5135, RUS white_sea 0.5039 and 0.4893, YEM hormuz 0.5000, YUE ganges_delta 0.5004, YAO ethiopia 0.5000, C09 laplata 0.5000, TUR comorin_cape 0.4899); the three others are TUR gujarat 0.529, TUR the_moluccas 0.639 (S79 -> S80, embargo and ship changes) and MOR safi 0.909. Stopping: 6 of 12 give 1.9985-2.0000 (AYU malacca and ganges_delta, YEM hormuz, FRA genua, ETH gulf_of_aden, C11 mexico), RUS white_sea 2.049; the others are TUR venice 1.680, DLH lahore 1.722, RUS baltic_sea 1.904, C11 mississippi_river 2.537, TUR ragusa 2.832, at nodes where embargo power or the control is loose. So the factor also shows up as a doubling when a country stops collecting away. Confidence for the switch pattern: `inferred` (consecutive saves of one campaign, controls not perfect); the corpus-wide claim C-01 stays `confirmed`.

Unverifiable here: the cause of the TUR crimea jump; whether the exceptions (MOR safi, TUR the_moluccas) are embargo effects.

## Update 2026-10-05 - Venice series U07-U30 (new game, VEN, 1444.11.11 to 1445.07.02)

Status: scripts `backend/scripts/research/venice_c_away.py`, `venice_c_pretick.py`, `venice_c_pretick_corpus.py`, `venice_c_ver4.py` (E), `venice_c_ver5.py` (4); loader `venice_load.py`, independent regex readers `venice_c_raw.py`. Labels: `confirmed` = whole set, exceptions listed. The series is one hands-off game of VEN (24 saves); the away collectors below are the AI countries' merchants, VEN itself never collects away (its three merchants steer).

### VA-1 Away collectors of AI countries in a 1444 game are halved: the factor 0.5 holds at md about 1.0
Claim: 449 entries with `has_trader`, no `type`, a `money` key and no `has_capital` (23 countries, 25 distinct country-node pairs, saves 1444.12.1 to 1445.7.2) have `max_demand` = 0.5 x a class value of the same country in 438 cases (tolerance 0.0011 on the half); the base is the country's foreign-class value, or, at a node where the country owns `top_provinces[0]`, its top-node class value.
Source: `venice_c_away.py` (blocks 'refined'), independent `venice_c_ver4.py` E (438 of 449: md x 2 equals one of the country's own class values within 0.0022).
Quote (1444.12.1): KTU ganges_delta 0.505 (class 1.009, half 0.5045), DLH lahore 0.505, KRC beijing 0.508 (1.016), PRO champagne 0.507 (1.014), ORI comorin_cape 0.523 (1.046), ARA genua 0.534 (1.067), GEN constantinople 0.569 (1.137), GEN crimea 0.559 and NOV white_sea 0.557 (both top-province nodes of the country: NOV class 1.114 -> 0.557). The additive form `md - 0.5` would give 0.509, 0.509, 0.516, 0.514, 0.546, 0.567, 0.637 for KTU, DLH, KRC, PRO, ORI, ARA and GEN constantinople: it is excluded by the 3-decimal data even at md about 1.0 (observed - additive = -0.004 to -0.068), while request_2 assumed that a late-game save was needed to tell the forms apart.
Exceptions: 11 entries, all GEN at crimea in 1445.2.1-7.2 (0.561/0.562, i.e. half of 1.122/1.124): GEN's stored class values in those saves do not contain 1.122 (home node genua 1.042 reduced by the LAN embargo, foreign 1.141); the composition of the base at that node is UNKNOWN (inferred: the top-node value without the embargo reduction of the home node).
Confidence: confirmed (438 of 449; the 11 are one country-node pair).

### VA-2 Start snapshots contain away collectors, but with neither money nor penalty until the first 1st
Claim: the collecting merchants away from the capital node that already exist in a start snapshot have no `money`/`total` and a full (not halved) `max_demand`; the first 1st of the game gives them money, the factor 0.5 and the +2 merchant power in `max_pow`.
Source: `venice_c_pretick_corpus.py` (78 start snapshots, parsed), `venice_c_pretick.py` (fresh game, regex), parsed cross-check for S01/U07/U09/U10.
Quote: 78 start snapshots: 5,028 collecting-away merchant entries (`has_trader`, no `type`, no `has_capital`): 0 with `money`, 5,028 with `max_demand` equal to a class value of their country, 0 at half of it. Fresh game: S01 and U07 (1444.11.11) 38 such entries, 0 with money; U09 (11.30, 15 of them reassigned by the AI) 23, 0 with money; U10 (12.1) the same 23 pairs, all with `money`; 19 of the 23 have `max_demand` exactly 0.5 x the U09 value (the other four moved to 0.55, 0.55, 0.61, 0.51 x because their class value changed at the same 1st too: GEN +0.202 etc.); `max_pow` +2.0 in 17 of the 23 (GEN crimea 60.728 -> 62.728). Home collectors (`has_capital`) already have money in U07: 560 of 560.
Confidence: confirmed. Consequence: the previous statement that away collectors exist "only in the played saves" (R07) and the goal's "snapshots cannot test it" are explained by the un-ticked state of a start snapshot, not by the campaign; a game advanced to its first 1st has them (VA-1).

### VA-3 Steering away is still not halved (replication of C-03)
Claim: 12,320 of 12,388 steering entries (`has_trader` and `type`) away from the capital node (S01, U07-U30) have `max_demand` at the class value (ratio 1.000 +-0.002); 0 at 0.5. The 68 others: ENG, GEN and LAN at champagne (nodes where an embargoer has own power, see R01 VS-5) and MNG at hangzhou and xian (top-province nodes: 1.126 is MNG's top-node class, while its home node beijing carries 1.326 = 1.126 + 0.2 home bonus, so the home value is the wrong baseline there).
Source: `venice_c_away.py` (last block). Confidence: confirmed for the 12,320; the 68 are explained by embargo and by the top-node class (inferred).

### VA-4 Capital versus main trade port: not testable here
Claim: in the 24 saves and S01 the `capital` and `trade_port` provinces of every country are identical (0 of 33,120 country-saves with a `trade_port` differ; 0 in S01); VEN's `has_capital` entry is at `venice` (24 of 24). So V4 of request_2 is unchanged: the question needs a country whose main port differs from its capital (R15).
Source: `venice_c_lib.py` based check (`capital` vs `trade_port`). Confidence: confirmed (as a statement about these saves).

### Verification 2026-10-05 (second pass, Venice series)
VA-1: parsed count (`venice_c_away.py`) and regex count (`venice_c_ver4.py` E, `venice_c_ver5.py` 4) agree: 449 entries, 438 fitting, 25 pairs, 23 countries. VA-2: the parsed counts (S01 38/0, U07 38/0, U09 23/0, U10 23/23) and the regex counts (`venice_c_pretick.py`: 38 with money 0; 23 with money 23; home 560/560; 19 at 0.5, max_pow +2.0 in 17) agree; the 78-save figure (5,028/0/0) was computed once with the parser only. VA-3: computed once with the parser (`venice_c_away.py`); the MNG explanation checked on the raw rows (hangzhou 1.126, xian 1.126, beijing 1.326).

## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R02-1 Switching one merchant to collecting away halves `max_demand` at that node only
Claim (P03): VEN's ragusa merchant switched from steering to collecting away: ragusa `max_demand` 1.036 -> 0.518 (exactly x0.5), `max_pow` unchanged (the merchant term stays, R06), new `total` 0.481 and `money` 0.634 at ragusa; the home bonus drops to 0 (R01 V2-R01-4). This is the controlled single-change pair asked for (same game and date, one merchant switched, unembargoed foreign node). Confidence: confirmed.

### V2-R02-2 `has_capital` with capital and trade port moved together (inconclusive)
Claim (E19): moving the capital from Venezia (112) to Padova (4729) moved `trade_port` too; `has_capital` stays at venice (both provinces are in the venice node). Whether `has_capital` follows the capital or the trade port is therefore not decided. VEN `province_power` at venice falls by 0.200 at t2. Confidence: confirmed for what was observed; the question stays open.

## Update 2026-10-08 - experiment round 2

Source: 27 single-change jobs run in the game by the automation (`tools/EU4-game-automation/experiments/round2/`: `PLAN.md`, `RESULTS.md`, scripts `analysis/`); saves under `round2/out/<id>/` (t1 = 1445.1.1, t2 = 1445.2.1; all dated, player and plain text checked). Controls as in round 1 (E01c / E01d on the E00 base) plus R2-C-U10, R2-H-MAM-C, R2-H-TUR-C, R2-C-NED18. **Void:** every merchant recall by save patch (R2-B5a, R2-B4, R2-B5c, R2-H-MAM-B1, R2-H-TUR-B1 and the recall half of R2-B5b / R2-H-MAM-B2): the patched save has no merchant at the node, t1 has it again (cause unknown); the embargo (R2-EMB) and privateer (R2-PRIV) patches are dropped on load; R2-TC added nothing (no territory province). No claim below rests on a recall.

### V4-R02-1 The home node is the node of the main trade port
Claim (R2-PORT): moving only `trade_port` 112 (Venezia, venice node) -> 4753 (Zara, ragusa node), capital unchanged, moves `has_capital` to VEN's ragusa entry; ragusa `max_demand` 1.036 -> 1.213 (home value), `max_pow` +5.000 (`TRADE_CAPITAL_POWER = 5.0`, defines.lua 1195); the merchant still collecting at venice is now away: `max_demand` 1.213 -> 0.507 (about 0.5 x 1.013). R2-CAP: `set_capital` moves `trade_port` with it (as E19). Answers R15 Q2 (a)/(b) for the save: the main trade port decides. Open detail: venice `max_pow` falls by 10.000 (5 = capital power, 5 unexplained). Confidence: confirmed (one country).
