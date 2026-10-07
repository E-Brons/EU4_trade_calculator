# R14 response 1 - Intervention-pair saves (data-based points only)

Answers only the parts of `R14_intervention_saves_request_1.md` that the fixture saves can settle: Q1 (facts of the matrix, checked in the saves), Q2 (the numbers a reviewer will see), Q3 (inland ships, observation only), Q5 (what the saves record about the random generator). Everything about in-game steps, UI paths, console commands, control timing, naming/checklist and quotes is **not** answered (see the end). Scripts: `backend/scripts/research/r11_r14_matrix.py`, `r11_r14_free.py`, `r11_r14_free2.py`, `r11_r14_md.py`, `r11_r14_seed.py`, `r11_r14_misc.py`. Source of every claim is the save corpus plus that script; Quote = the save values.

## Q1 - Corrections to the matrix that the saves prove

All start rows use the 35 saves dated 1444.11.11 (S01-S35). Home node = the node whose country entry has `has_capital`; links = `outgoing` of the node in `data/tradenodes.json` (the project's node graph); "placed" = nodes where the entry has `has_trader`; action = `type` present (steer), `total` present (collect), neither (present only).

| ID | Draft says | Data (save) | Verdict |
|---|---|---|---|
| IV-01 | FRA home node = `english_channel` | S03 FRA: `has_capital` only at `champagne` (`province_power 65.051, total 2.474`); FRA at `english_channel` is a bare `max_demand 1.053` stub | draft wrong; FRA home = champagne (also contradicts IV-14 inside the draft). The node `english_channel` is an end node (0 outgoing links) and is ENG's home (S02: `has_capital`, `province_power 177.336`, `total 7.552`) |
| IV-01/02/03/04/05/06/07/12/14 | "assign a free merchant" | In every one of these saves the named country has **no free merchant**: S02 ENG, S03 FRA, S04 CAS, S05 POR, S06 HAB, S14 TUR each have 2 envoys, both placed (`merchants.envoy` entries with `action = 2`, and 2 nodes with `has_trader`) | the B change needs "recall, then place" (two changes) or a different country; see free-merchant list below |
| IV-02 | ENG collects away at `genua` | S02 ENG: merchants steer at `lubeck` and `champagne`; ENG at `genua` is a stub (`max_demand 1.067`, no power) | premise needs a recall first |
| IV-03 | CAS (`tunis`) "with province power" | S04 CAS already **steers** at `tunis` (`type 1`), `province_power` absent, only `prev 25.997`; CAS home = `sevilla`; `tunis` has 3 links (sevilla, valencia, genua) | not a "none -> collect" case and no province power there |
| IV-04 | TUR `alexandria`, "2-link node", merchant none -> steer | S14 TUR already **steers** at `alexandria` (`type 1`, `steer_power` absent = first link, `prev 19.769`); `alexandria` has **3** links (constantinople, venice, genua) | wrong start state, wrong link count |
| IV-05/06 | POR `safis`, 3-link node, `sevilla` -> `bordeaux` | the node id is `safi`; it has **1** outgoing link (`sevilla`); POR already steers there and at `tunis`; `bordeaux` is not a link of `safi` | wrong node. Link counts in the project graph (`data/tradenodes.json`, consistent with the save's `incoming.from` in S03): 1 link 21 nodes, 2 links 32, 3 links 22, 4 links 2 (`california`, `ivory_coast`), 0 links 3 (`english_channel`, `genua`, `venice`). 3-link nodes include `tunis`, `alexandria`, `wien`; 2-link nodes include `champagne` (genua, english_channel) and `north_sea` (english_channel, lubeck) |
| IV-07 | HAB `wien` Collect -> Steer, "`max_demand` penalty removed" | S06 HAB: `wien` is the capital node (`has_capital`, `total 1.302`, **no `has_trader`**: the capital collects without a merchant); HAB's merchants steer at `pest` and `krakow`. A home node has no away penalty to remove | wrong: nothing to switch at wien and no penalty to remove there |
| IV-08 | FRA + SCO steer the same link at `north_sea` | S03: SCO exists, home `north_sea`, its merchant **collects** there; FRA has only a stub at `north_sea` (`max_demand 1.053`) | wrong premise (SCO collects, FRA has no power there) |
| IV-12 | ENG ships at `lubeck` "without placing a merchant" | S02 ENG already has a **steering** merchant at `lubeck` (`has_trader`, `type 1`, `prev 35.467`) | not a passive node; choose a node where the country has an entry and no `has_trader` |
| IV-14 | recall FRA merchant at `champagne` | S03 FRA has no merchant at `champagne` (home, `has_trader` absent); its merchants are at `rheinland` and `bordeaux` (steering) | node wrong for the recall |
| IV-17 | POR `ivory_coast` | S05 POR at `ivory_coast` is a stub (`max_demand 1.029`), 4 outgoing links | exists, but POR has no entry/power there (trade company region state not checked here) |
| IV-18 | PRU at 1444 | S03/S06: `countries.PRU` exists but has no cities (`num_of_cities` absent), no envoys, no `has_capital`: PRU does not exist in 1444. S62 (1744.11.11): PRU home `saxony`, 26 cities, 6 envoys. BRA in 1444: home `saxony`, 8 cities, 2 envoys steering at `krakow`, `wien` | PRU needs a start of 1744 (S62) or later; BRA works at 1444 (home saxony) |
| IV-20 | "OPM" | `OPM` is not a key of `countries` in S03/S06 | a placeholder, not a tag |
| IV-15/16 | CAS vs ARA, SCO -> ENG | CAS, ARA, SCO, ENG all exist in 1444 (ARA home `valencia`, 25 cities; SCO 9 cities); ARA steers at `sevilla` and has a merchant that does nothing at `genua` | tags exist; whether the actions are available is not testable from the saves |
| IV-13 | ENG 1550 with DIP tech 15 | the corpus has ENG at 1444, 1526, 1644 only | no such start save; not checked further |

Free merchants. Evidence for "free": a country's envoys with `action = 2` equal its nodes with `has_trader` in 22,750 of 22,820 country-saves (1444 start saves, all countries with cities; the 70 exceptions include CHT and MIS), so an envoy without `action` is an unplaced merchant. Among the 35 player countries of the 1444 saves, only these have one free merchant: RAG (S10), ASK (S21), ETH (S28), KON (S30), ZAN (S31), KTS (S32), AZT (S33), CSU (S34), ONO (S35). The other 26 (incl. ENG, FRA, CAS, POR, HAB, TUR, VEN, GEN) have none. SCO (S03 AI country) has 2 envoys and 1 placed, so it has one free merchant; in S03, 486 countries have more envoys than nodes with `has_trader` (mostly small AI countries).
Confidence: confirmed (read directly; the PRU / OPM / free-merchant counts are corpus-wide).
Not changed here: the date convention (A on 1444.12.01 vs start 1444.11.11): the data gives only the start date 1444.11.11 of all 35 start saves; which day is "after a tick" is an R12 question.

## Q2 - What a reviewer sees for the away penalty (additive vs multiplicative)

Claim C-01: with the saved `max_demand` values, the two hypotheses give nearly the same number in a 1444 start and clearly different numbers only in a late-game save.
Formula: B(multiplicative) = `max_demand_C x 0.5`; B(additive) = `max_demand_C - 0.5`.
Source: `r11_r14_md.py`. Quote (real values):
- S02 ENG at `genua`: C `max_demand 1.067` -> multiplicative 0.5335, additive 0.567 (difference 0.0335)
- S04 CAS at `tunis`: C `1.054` -> 0.527 vs 0.554 (difference 0.027)
- In 1444 start saves the player's `max_demand` ranges only 0.929 (HSA, S08) to 1.138 (MNG, S20) (ENG 1.055-1.067, CAS 1.039-1.054, HAB 1.04-1.046, TUR 1.051-1.083), so the two predictions differ by `0.5 x (max_demand - 1)` in absolute value, at most 0.07 (0.0195-0.0415 for the four named countries), and any other small change in `max_demand` (the value also differs between home and away nodes, ENG 1.055 at home vs 1.067 elsewhere) can hide it.
- S79 TUR (1665.4.22) has `max_demand 2.11` at e.g. `african_great_lakes`, `kongo`, `zambezi`, `patagonia`, `amazonas_node`, `rio_grande`, `james_bay`, `california` (no province power, not steering, not collecting): if the merchant there started collecting, multiplicative B = 1.055, additive B = 1.61, a difference of 0.555. S80 TUR has values up to 2.039.
Consequence: the pairs IV-02, IV-03 and IV-07 only discriminate additive from multiplicative if made in a late-game save (such as S79/S80, which are TUR) or with a country whose `max_demand` is well above 1.1; in a 1444 save they would need the third decimal. The home-node `max_demand` (1.055) is lower than the away stub (1.067) in ENG S02, so "home" and "away" differ by more than the penalty-free baseline: record both nodes' values in C.
Confidence: confirmed as arithmetic on saved values; which hypothesis is true is not answered here (R02 integrates the multiplicative one; this response does not test it). The name and quote of `TRADE_NON_CAPITAL_OFFICE` are not answered here.

## Q3 - Inland ships (observation only)

Claim C-02: no save shows ships at an inland node. In S79/S80 (the only saves with ships, 216 entries) no entry with `light_ship` is at a node flagged `inland` in `tradenodes.json`, and no protect-mission fleet targets an inland node (`r11_r14_misc.py`, `r11_r14_nonlight.py`). This says nothing about what the game shows if the order is attempted. Confidence: inferred (absence in data). The additional pairs (embargo off, transfer off) are design work and are not answered.

## Q5 - Determinism: what the saves record

Claim C-03: a save stores the random generator state at top level: `multiplayer_random_seed` and `multiplayer_random_count`; `decision_seed` appears 668 times and `seed` 816 times inside country/province blocks of one start save (S14).
Source: `r11_r14_seed.py`. Quote:
- All 35 start saves (1444.11.11) have different `multiplayer_random_seed` (35 distinct) and counts 161,807-162,914 (34 distinct values), e.g. S02 ENG `1303332874 / 161807`, S03 FRA `3828062799 / 162087`.
- S79 (1665.4.22), S80 (1682.4.18), U01 and U02 share the seed `2624455014` (same campaign); `multiplayer_random_count` = 6,464,168 (1665.4.22) and 38,897,052 (1682.4.18). That is about 32.4 million draws in the 6,201 days between them (EU4 years have 365 days: 17 years less 4 days), about 5,230 draws a day, so the counter advances continuously with play.
- U02 has the same `trade` block as S79 and U01 the same as S80 (equal parsed trees), i.e. re-saving without playing does not change the trade data.
What this does NOT show: whether B and C diverge (that depends on whether the intervention changes the number of draws, unknown) and whether AI decisions use this generator. Determinism of B vs C is UNKNOWN from the data.
Cheapest experiment (design, not data): two C saves from the same A and compare `multiplayer_random_count` and the 5-node divergence fields; if they are equal, then B vs C differences beyond the intervention can be attributed to the intervention. Confidence: confirmed for the recorded fields, UNKNOWN for determinism.

## Not answered (needs an outside source, game UI knowledge or new saves)

- Q1: the full re-issued 20-pair table (this response only lists the proven corrections); valid replacement countries/nodes beyond those named above were not searched.
- Q2: the define name and quote.
- Q3: the new pairs for embargo off and transfer off (no save in the corpus records an embargo or transfer being switched off).
- Q4: every per-pair detail: in-game steps, control design, notes (UI/console knowledge, not in saves). The "must not change" fields would need the interventions.
- Q5: the divergence check tolerances and the choice of distant nodes (`beijing`, `malacca`, `peru`, `zambezi`, `monomotapa`) need the node graph and an experiment.
- Q6: naming and the checklist (conventions, not data).
- Q7: quotes and defines (`PLACED_MERCHANT_POWER`, steering tiers, `CAPITAL_NODE_POWER_BONUS`, `VAL_TRANSFER_BONUS`).

## Verification (date 2026-10-04)

Independent re-computation in `backend/scripts/research/ver_r14.py` and `ver_r14b.py` (new code, not the author's `r11_r14_*.py`), over the 82 saves.

Re-run and matching (no change needed):
- FRA S03: `has_capital` only at `champagne` (`province_power 65.051`, `total 2.474`), stub `max_demand 1.053` at `english_channel`; ENG S02 home `english_channel` (`177.336`, `7.552`); `english_channel` has 0 outgoing links (also `genua`, `venice`).
- Graph consistency: the reverse of S03's `incoming.from` equals `data/tradenodes.json` outgoing for all 80 nodes. `safi` has one link (`sevilla`), `tunis` (sevilla, valencia, genua), `alexandria` (constantinople, venice, genua), `wien` (venice, rheinland, saxony), `ivory_coast` 4 links, `champagne` (genua, english_channel), `north_sea` (english_channel, lubeck).
- CAS S04 steers at `tunis` (`type 1`, `prev 25.997`, no `province_power`), home `sevilla`; TUR S14 steers at `alexandria` (`type 1`, `prev 19.769`, no `steer_power`); POR S05 steers at `safi` and `tunis`, stub at `ivory_coast` (`max_demand 1.029`); HAB S06 `wien` is the capital (`total 1.302`, no `has_trader`), merchants at `pest`, `krakow`; ENG S02 steers at `lubeck` (`prev 35.467`) and `champagne`, stub `max_demand 1.067` at `genua`; FRA S03 merchants at `rheinland`, `bordeaux`; SCO S03 home `north_sea`, collects there; ARA home `valencia` (25 cities), steers at `sevilla`, idle merchant at `genua`.
- PRU exists as a key without cities in S03/S06, with 26 cities and 6 envoys and home `saxony` in S62; BRA in S03 has 8 cities, home `saxony`, steers at `krakow` and `wien`; `OPM` is not a key in S03/S06; ENG only at 1444 (S02), 1526 (S43), 1644 (S52).
- Free merchants: envoys with `action = 2` equal nodes with `has_trader` in 22,750 of 22,820 country-saves with cities (70 differ, incl. CHT, MIS); the 6 named players (S02-S06, S14) have 2 envoys, both placed; exactly the 9 listed players (RAG, ASK, ETH, KON, ZAN, KTS, AZT, CSU, ONO) have a free merchant among the 35 start players; SCO 2 envoys / 1 placed; 486 countries in S03 have more envoys than placed nodes.
- `max_demand`: ENG 1.055-1.067, CAS 1.039-1.054, HAB 1.04-1.046, TUR 1.051-1.083; the arithmetic 0.5335 / 0.567 / 0.527 / 0.554 / 1.055 / 1.61; S79 TUR `max_demand 2.11` at the eight listed stub nodes (42 TUR nodes have 2.11); S80 TUR up to 2.039.
- Seeds: 35 distinct seeds and 34 distinct counts in the 35 start saves; S02 `1303332874 / 161807`, S03 `3828062799 / 162087`; S79, S80, U01, U02 share `2624455014` with counts 6,464,168 and 38,897,052; `decision_seed` 668 and `seed` 816 occurrences in S14; U01/U02 have the same parsed `trade` and `countries` blocks as S80/S79.

Corrected:
- Player `max_demand` range at 1444: "1.039-1.138" -> 0.929 (HSA S08) to 1.138 (MNG S20); the claim "the two predictions differ by less than 0.06" -> they differ by `0.5 x |max_demand - 1|`, at most 0.07 over all players (0.0195-0.0415 for ENG, CAS, HAB, TUR). Why: recomputed over all 35 start players.
- Start-save `multiplayer_random_count` range: 161,807-162,370 -> 161,807-162,914 (max in S17). Why: regex over the 35 start saves.
- Days between S79 and S80: "roughly 6,205" -> 6,201 (17 years of 365 days less 4 days); draws per day 5,200 -> 5,230.
- IV-05/06 row: the list "3-link nodes: tunis, alexandria, wien; 4-link: ivory_coast; 2-link: champagne, north_sea" read as exhaustive -> they are examples: 22 nodes have 3 links, 32 have 2, 2 have 4 (`california`, `ivory_coast`), 21 have 1, 3 have 0.

Could not be verified here:
- "Whether B and C diverge" / determinism: not derivable from saves (the response already says UNKNOWN).
- The 365-day year is the game calendar's rule, not read from a save.
- Whether a merchant can be placed in a given 1444 node (game UI rules) and the tag/date premises of IV-13 and IV-15/16 beyond "tag exists".

## Update 2026-10-05 - Venice series U07-U30 (what the first intervention saves show)

Data: the Venice series U07-U30 (player VEN, game 1.37.5, non-Ironman plain-text saves, same mod list as S01, new campaign started 1444.11.11): U07 1444.11.11, U08 11.14, U09 11.30, U10 12.01, U11 12.02, U12 12.11, U13 12.31, U14 1445.01.01, U15 01.02, U16 01.15, U17 01.24, U18 01.30, U19 01.31, U20 02.01, U21 02.03, U22 02.10, U23 02.17, U24 02.28, U25 03.01 (U07-U25: no player action at all); then U26 03.31 (all three VEN merchants recalled during March), U27 04.01, U28 05.01 (ragusa merchant sent again), U29 06.01 (alexandria), U30 07.02 (wien). Scripts: `backend/scripts/research/venice_a_*.py` (loader `venice_load.py`), second pass `venice_a_ver.py` (raw text diff of the `trade` block, own Decimal loop for `prev`).

### V-R14-1 Which saves count as "after a tick"
Claim: a `trade` block is the result of a monthly computation only from the first 1st of the game (1444.12.1, U10) on; the bookmark state (U07, 1444.11.11, also U08/U09 up to 11.30) is an initial state, not a tick result: `max_pow` has no merchant term (R06 V-R06-1), the stored `prev` follows the bookmark weights (R05 V-R05-1), and 19,074 `max_demand` fields change at the first 1st. All saves of one month after a 1st carry the same computed values (R12 V-R12-1), so any day after a 1st is as good as the 1st for reading computed values; the merchant flags are current on the save day.
Confidence: confirmed (one game).

### V-R14-2 Comparison of two fresh games
U07 (new game, VEN, 1444.11.11, nothing touched) differs from the older start snapshot S01 (same tag/date/version/mods) in 3,798 node fields, 2,686 of them `max_demand` (ratio 0.971 to 1.020, median 0.995): two identical fresh games are not identical in their stored `max_demand`; see the R01 Update of the same date. Determinism of A -> B/C (request_1 Q5) is therefore not testable as planned: UNKNOWN.

### V-R14-3 First intervention performed
Recall of all three merchants (U25 -> U26/U27) and re-sending them one per month (U28, U29, U30) is the pair/sequence IV-14-style "merchant none -> steer": results in R08/R09/R07 Updates of the same date. Not done yet: embargo, ships, privateers, trade company, idea/tech, transfers, away collection.

## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R14-1 B and C diverge given the same A
Claim (E01a vs E01b, two runs from the same save): 4,859 of 73,073 trade-block fields differ at t1 and 8,029 at t2, mostly other countries' `max_demand` and AI-driven fields; VEN's own entries are identical (101 of 103 fields across the four controls; venice `money`/`total` +-0.6 %). So intervention pairs must compare the changed country's fields (or identities), not whole-world diffs. Confirmed.

### V2-R14-2 Pairs now done
Single-change pairs were run for: away collection (P03), steering link change (P01), trade steering (E08), trade efficiency (E06), trade-power modifiers (E03-E05), ship modifier (E07) and fleet move (P05), province modifiers, marketplace, mercantilism, autonomy (E09, E17, E12, E18), merchant capacity (E13), technology (E10, E11), idea group (E22), subjects (E20a/b/d), a vanished country (E21). Void: E16 (no-op), E20c (relation not created), P02 (recall did not hold), P06 (country too small for the propagation question), E19 (capital and trade port moved together). Results per topic in the R01-R13 responses.
