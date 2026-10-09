# R11 response 1 - Ships and trade power (data-based points only)

Answers only the points of `R11_ships_and_trade_power_request_1.md` that the fixture saves can settle. Every number comes from a script run over the saves (scripts in `backend/scripts/research/r11_r14_*.py`: `fleets`, `reconcile`, `fleetflags`, `four`, `ratio`, `ratio2`, `leader`, `home`, `misc`, `nonlight`, `summary`). Source of every claim below is "the save corpus + that script"; the Quote is the verbatim save data.

**Where the data is.** Only the 4 ticked saves carry ship data: S79 (1665.4.22, 112 country-node entries with `light_ship`), S80 (1682.4.18, 104), and the user cases U02 / U01, which are identical to S79 / S80 (`trade` block equal, ship entries equal). The 78 game-start snapshots contain **0** entries with `light_ship`. So all ship statements rest on 216 entries of two TUR campaign saves (same `multiplayer_random_seed`), not on 80 independent saves.

**Where ships are stored (used by Q1, Q5).** Not in the `trade` block. `countries.<TAG>.navy` is a list of fleets; each fleet has `ship = [ {id name home type morale ...} ]` and, for a fleet on protect-trade, `mission = { protect_mission = { retreat_port was_safe_retreat_port node trade current_route_target current_cycle_begin on_my_way } }`. `protect_mission.node` is the **1-based** index into the save's trade node list (the same indexing as `incoming.from`).

## Q1 - Fleet arithmetic: the real assignment of TUR's ships (S79)

Claim C-01: the six node rows are reproduced exactly by the fleets' `protect_mission.node`; TUR has 100 light ships on protect missions, 98 are counted in node entries, 2 are not.
Formula: `light_ship(node) = number of light ships in the fleets with protect_mission.node = node (and counted, see Q4)`; `ship_power = sum(base trade_power per type)` (factor 1.0 for all TUR rows, see Q3).
Applies when: S79 (and U02), TUR.
Source: save corpus, `r11_r14_reconcile.py`, `r11_r14_fleetflags.py`.
Quote (fleet name: node index -> node name, types; `trade_power` from `data/game/light_ships.json`: early_frigate 3.0, frigate 3.5):

| fleet (country.navy[]) | `protect_mission.node` | node | ships | base sum | entry in node (`light_ship`, `ship_power`) |
|---|---|---|---|---|---|
| Basra Trade Fleet | 30 | malacca | 20 early_frigate + 4 frigate | 60 + 14 = 74 | 24, 74 |
| Zeila Donanmasi | 35 | comorin_cape | 13 frigate | 45.5 | 13, 45.5 |
| Kizildeniz Donanmasi | 35 | comorin_cape | 1 early_frigate | 3.0 | **not counted** |
| Suhar Donanmasi | 43 | basra | 4 frigate | 14 | 4, 14 |
| Sinop Donanmasi | 49 | crimea | 1 early_frigate | 3.0 | 1, 3 |
| Venice Trade Fleet | 78 | genua | 13 early_frigate + 7 frigate | 39 + 24.5 = 63.5 | 20, 63.5 |
| Tirhala Donanmasi | 79 | venice | 31 early_frigate + 5 frigate | 93 + 17.5 = 110.5 | 36, 110.5 |
| Karadeniz Donanmasi | 39 | gulf_of_aden (TUR steers there) | 1 frigate | 3.5 | **no `light_ship` in the TUR entry** |

Totals: early_frigate 20+1+1+13+31 = 66 and frigate 4+13+4+1+7+5 = 34, i.e. all 100 of TUR's light ships (66 + 34, as in the goal) are on protect missions. The draft's assignment (67 early frigates, 31 frigates) is impossible (rule 5: contradicted). The "98 of 100" is exactly the two ships above that have a protect mission but do not appear in any node entry. The assignment reproduces every one of the six rows to the last digit; it is unique here because the node index is stored.
Confidence: confirmed (6/6 rows; corpus-wide: of 216 ship entries, 215 have exactly one subset of the node's fleets that reproduces `light_ship`, 1 (S80 SPA malacca) has two subsets; the verification pass resolved that one: its third fleet "3rd Fleet" has no `on_my_way` key, and the other two fleets give exactly 5 ships / 16.5 = the entry).
Caveats: why exactly those two fleets are not counted is Q4.

## Q2 - Which ship types count (data part only)

Claim C-02: only barque, caravel, early_frigate, frigate (four of the six types in `light_ships.json`; heavy_frigate and great_frigate never occur on a protect mission in the corpus) contribute to `light_ship` and `ship_power`. Other types inside a protect fleet contribute nothing.
Source: `r11_r14_misc.py`, `r11_r14_nonlight.py`. Types in all protect-mission fleets (S79+S80): early_frigate 433, frigate 759, caravel 265, barque 342, galiot 3, galleon 3, galleass 9.
Quote: S79 BLG, fleet "2nd Fleet" at venice: `{frigate: 3, galiot: 3}` -> entry `light_ship 3, ship_power 10.5` (= 3 x 3.5). S80 YUE, fleet "3rd Fleet" at canton: `{early_frigate: 2, galleon: 3, galleass: 9}` -> entry `light_ship 2, ship_power 6.0` (= 2 x 3.0).
TUR's galleys, galiots, galleasses, carracks, galleons, merchantmen and war galley are in fleets **without** a `mission` key (S79: "Ege Donanmasi", "1st Royal Navy", "2nd Gulf Navy", "3rd Gulf Navy"), so they are not on protect missions; the corpus shows no case where they add power.
Confidence: confirmed for the 4 light types plus "galiot/galleon/galleass add 0" (2 cases, 15 ships); UNKNOWN for `trade_power` in `common/units` (needs the game files, not answered here).

## Q3 - What raises power per ship above the base value

Claim C-03: `ship_power = f x sum(base trade_power of the counted light ships)`, with a per-entry factor `f` that takes only the values **1.0, 1.05, 1.1, 1.2** and is never below 1.
Source: `r11_r14_ratio.py`, `r11_r14_summary.py`.
Quote / evidence (216 entries, 215 uniquely fitted): f = 1.0 in 203, 1.1 in 9, 1.2 in 2, 1.05 in 1. The non-1 entries:
- S79 SPA ivory_coast: 3 frigate, `ship_power 11.025` = 10.5 x 1.05 (this is the corpus maximum 3.675 = 3.5 x 1.05)
- S79 / S80 LAI, VIL, VNL polynesia_node (barque/caravel/early_frigate mixes): 25.85 = 23.5 x 1.1; 22.0 = 20 x 1.1; 17.6 = 16 x 1.1
- S79 MNA, TDO philippines: 13.2 = 12 x 1.1; 4.4 = 4 x 1.1
- S79 DAN lubeck: 123.2 = 112 x 1.1 (20 early_frigate, 12 frigate, 4 caravel)
- S79 / S80 SAM polynesia_node: 35.4 = 29.5 x 1.2
f is **multiplicative** over all ship types in the entry (it multiplies caravels and barques by the same factor, so a caravel-specific +0.33 is not visible: LAI's 3 caravels + 8 barques give exactly 1.1 x base), and it is **not** a per-country constant: DAN has f = 1.0 at north_sea and st_lawrence and 1.1 at lubeck; SPA has 1.0 at malacca, genua, sevilla and 1.05 at ivory_coast (S79).
Confidence: confirmed as a description of the data (215/215); the cause is UNKNOWN.
**Updated 2026-10-05:** the cause is now partly identified (national idea sets for leaderless fleets, leader `maneuver` for leader fleets); explanations (a) and (d) listed below as rejected are superseded. See the section 'Update 2026-10-05' at the end of this file.
Explanations tested and rejected by the data (not sourced alternatives): (a) a leader in the fleet (10 of the 12 non-1 entries have no fleet with `leader`; none of the 203 f = 1 entries has one, so the 2 with a leader are the only support and 10 contradict); (b) the ships' `home` port inside the node (10 of the 12 non-1 entries have all ships homed in the node, 1 none, 1 mixed; but 82 entries with f = 1 have all ships homed there too); (c) ship type; (d) a country constant (DAN, SPA); (e) `trade_company_region` (all 12 non-1 entries are in such nodes, but so are 158 of the f=1 entries, so it does not discriminate); 11 of the 12 are the country's home (`has_capital`) collecting node, which also fails to discriminate (62 home collectors in S79 and 51 in S80 have f = 1).
What would settle it: a country modifier readout is not in the save (goal), so an intervention pair (add one ship / change a policy) or the game's modifier list for LAI/SAM/DAN/SPA at those dates.
Caveats: `light_ship_efficiency_factor` of the draft does not exist in any form in the data: f is never below 1. No name for the modifiers (`global_ship_trade_power` etc.) can be tied to f from the saves (needs sources, not answered).

## Q4 - Limits (data part only)

C-04 (num_ships_protecting_trade): `countries.<TAG>.num_ships_protecting_trade` equals the number of light ships on protect-mission fleets in 143 of 145 country-saves (S79+S80), and equals the sum of the node entries' `light_ship` in 139 of 145. Differences (country, nps, sum of `light_ship` in nodes, light ships on protect missions): S79 TUR 98, 98, 100; S79 C03 17, 15, 17; S79 SPA 70, 53, 70; S79 DAN 41, 39, 41; S79 GBR 40, 35, 40; S79 HOL 8, 7, 8; S80 SPA 84, 81, 84; S80 BNG 37, 37, 38. So `nps` is a count of fleet ships, not of trade power entries, and it does not drop to the node total for TUR (98) the way the other countries do (it does for the 2 TUR ships not counted); why is UNKNOWN. Confidence: confirmed as counts.
C-05 (not-counted fleets): a protect-mission fleet is missing from the node entries in 14 of 239 fleets with a unique fit. In 10 of them the mission has **no `on_my_way` key** (an 11th fleet without the key, S80 SPA "3rd Fleet" at malacca, sits in the group that was ambiguous above and is also not counted, so 11 of the 15 uncounted fleets of 242 lack the key); all 225 counted fleets (227 with the SPA malacca pair) have `on_my_way = false` (and every fleet with the key has the value `false`: 121 in S79, 110 in S80). The other 4 (S79 C03 "1st Fleet", "9th Fleet" at mexico; TUR "Kizildeniz Donanmasi" at comorin_cape and "Karadeniz Donanmasi" at gulf_of_aden) have `on_my_way = false`, are moving (`path` present, `movement_progress` 5.1-32.6, `current_cycle_begin` 1-3) like counted fleets, and nothing in `ship`, `mission` or fleet keys separates them (`r11_r14_four.py`). Candidate (not testable here): ships assigned after the last monthly tick (S79 is dated the 22nd). Rule `on_my_way` present is necessary (227/227 counted fleets, after the SPA malacca resolution) but not sufficient (4 fleets have it and are not counted). UNKNOWN; settles with a save on the 1st right after a tick, or the same fleet in two saves.
C-06 (cap per node): there is no cap at 24 or 36. Largest entries: S80 TUR the_moluccas 65 ships, S80 TUR comorin_cape 60, S79 SPA sevilla 42, S79 TUR venice 36, DAN lubeck 36. The goal's "Malacca 24, Venice 36" are TUR's counts in S79, not caps (rule 5). Confidence: confirmed (no cap below 65 observed; a higher cap is not excluded).
C-07 (organisation / port): counted light ships have `morale` between 2.08 and 5.729, and `ship_power` equals f x base exactly in all 215 entries, with f never below 1: no organisation-, damage- or port-dependent reduction is visible (28 of the 1,799 light ships on protect missions carry a `strength` key; DAN lubeck, TDO have such ships and are among the f = 1.1 entries). Confidence: inferred (maximum morale is not in the data, so a threshold that never triggered is not excluded). The quotes for `TRADE_SHIP_MAX_DAYS_IN_PORT` / `TRADE_SHIP_ORG_LIMIT` are not answered here.
C-08 (inland): 0 of 216 entries with `light_ship`, and 0 protect-mission fleets (S79+S80), target an inland node. Confidence: confirmed as an observation; it does not say what the game does when the order is tried.

## Q5 - Storage of the assignment

Claim C-09: the assignment is `countries.<TAG>.navy[].mission.protect_mission.node` (1-based node index), and the fleet's ships are `navy[].ship[]` with `type`. The draft's `fleet = { mission = protect_trade target = <node_id> }` does not exist in the saves (rule 5): the key is `navy`, the mission is `protect_mission`, the target is a number.
Quote: S79 TUR `navy` entry `{ name="Basra Trade Fleet" ... mission={ protect_mission={ retreat_port=2713 was_safe_retreat_port=yes node=30 trade={1399 1359 ...} current_route_target=14 current_cycle_begin=2 on_my_way=no } } ship={ ... type="early_frigate" ...} }` and the node entry `malacca.TUR = { light_ship=24 ship_power=74 ... }` (node 30 = `malacca` in 1-based order).
Evidence: with the 1-based index, 100 of 119 (tag,node) pairs in S79 and 98 of 105 in S80 match exactly (count and base power); the remaining pairs are the f != 1 entries (Q3) and the not-counted fleets (Q4). The start snapshots have no `mission` on any fleet.
For a calculator: to move ships between nodes read `navy[].mission.protect_mission.node` and the ship `type`s of that fleet; add only fleets that satisfy Q4's condition; the per-node `light_ship` / `ship_power` is the output to compare. Confidence: confirmed (storage), see Q4 for the counting condition.

## Q6 - One more ship (data part only)

Claim C-10: adding one light ship of type T to a counted fleet at a node where the country already has ships changes `ship_power` by `f x base_T`, with `f = ship_power / sum(base)` of that entry, read from the save; `max_pow` then rises by the same amount if `max_pow` contains `ship_power` as the goal states, and `val` by `f x base_T x max_demand` (`val = max_pow x max_demand`, goal).
Confirmed: the `f x sum(base)` structure (215/215). UNKNOWN: `f` for a node where the country has no ships yet (f is not constant per country, Q3), the case of a ship that is not counted (Q4), and the ship type limits beyond Q2.
Source: `r11_r14_summary.py`.

## Not answered (needs an outside source or an intervention save)

- Q2: file and line of `trade_power` in `common/units` for each type (only the data effect is given).
- Q3: names and sources of `global_ship_trade_power`, `ship_trade_power_modifier`, `trade_power_in_fleet_modifier`, doctrines; the cause of f.
- Q4: quotes for `TRADE_SHIP_MAX_DAYS_IN_PORT`, `TRADE_SHIP_ORG_LIMIT`; why the 4 `on_my_way = false` fleets are not counted; why TUR's `num_ships_protecting_trade` excludes them.
- Q7: open sea vs coastal: the save has no coast/open-sea classification of nodes, so the data cannot separate them; needs a source for what `OPEN_SEA_MODIFIER` / `COASTAL_MODIFIER` affect.
- Q8: the copied quote in C-02 of the draft needs a real source.

## Verification (date 2026-10-04)

Independent re-computation in `backend/scripts/research/ver_r11.py`, `ver_r11b.py`, `ver_r11c.py`, `ver_r11d.py` (new code, not the author's `r11_r14_*.py`), over the 82 saves.

Re-run and matching (no change needed):
- Only S79 (112 entries), S80 (104), U02 (112), U01 (104) have `light_ship`; the other 78 saves have 0 entries; U02/U01 equal S79/S80 (parsed `trade` and `countries` blocks identical); the 78 start saves have no fleet with a `mission` key.
- Storage `countries.<TAG>.navy[].mission.protect_mission.node` (1-based); the quoted Basra Trade Fleet block (`retreat_port 2713`, `was_safe_retreat_port yes`, `node 30`, `current_route_target 14`, `current_cycle_begin 2`, `on_my_way no`).
- TUR S79: the eight-row fleet table (nodes, ship types, base sums, entries), 66 early_frigate + 34 frigate = 100 on missions, `num_ships_protecting_trade` 98, the two uncounted fleets (Kizildeniz at comorin_cape, Karadeniz at gulf_of_aden).
- `ship_power = f x sum(base)`: f histogram over the 215 uniquely fitted entries of S79+S80 = 1.0: 203, 1.1: 9, 1.2: 2, 1.05: 1, never below 1; the twelve non-1 rows (values, bases, factors) and the DAN / SPA per-node factors.
- Rejected explanations: leader in fleet (2 of 12 vs 0 of 203), ships homed in node (10 all / 1 none / 1 mixed vs 82 of 203), trade_company_region (12 of 12 vs 158), home collecting node (11 of 12 vs 62 in S79 and 51 in S80).
- Non-light ships add nothing (S79 BLG venice `galiot 3`; S80 YUE canton `galleon 3, galleass 9`); type totals over protect fleets (frigate 759, early_frigate 433, caravel 265, barque 342, galiot 3, galleon 3, galleass 9); TUR's four fleets without `mission` and their names.
- C-04 counts: `nps` = ships on missions in 143 of 145 country-saves, = sum of node `light_ship` in 139 of 145, and all eight listed exception triples.
- C-05 (14 of 239 fleets uncounted, 10 without `on_my_way`, 4 with it: C03 "1st Fleet" and "9th Fleet", TUR "Kizildeniz", "Karadeniz"; their `movement_progress` 5.097-32.568, `path` present, `current_cycle_begin` 1-3).
- C-06 caps (65, 60, 42, 36, 36), C-07 morale 2.08-5.729 and 28 of 1,799 ships with `strength`, C-08 no inland entries or fleets, C-09 "100 of 119 pairs in S79, 98 of 105 in S80 match exactly".

Corrected:
- C-01 / C-05: the one ambiguous group (S80 SPA malacca) is resolved by `on_my_way`: its "3rd Fleet" (1 frigate) has no key; the other two fleets give 5 ships / 16.5 = the entry. Consequence: 216 of 216 entries are uniquely fitted, 11 of the 15 uncounted fleets (of 242) lack the key, and the key is necessary for all 227 counted fleets. Old: "10 of 14", "225/225". Why: a fleet-level recount with the key as a filter.
- C-02 wording: "the types in `light_ships.json`" -> four of the six types in it (heavy_frigate and great_frigate exist in the file and never occur in a protect fleet). Why: the file lists six.

Could not be verified here:
- Base `trade_power` per type is read from the project file `data/game/light_ships.json` (the game files are not in the repo); the claim that galleys etc. have no `trade_power` is not tested.
- "Why the four fleets with `on_my_way` are not counted" and the cause of f stay UNKNOWN (as the response says); the claim "ships assigned after the last tick" is a hypothesis, untested.

## Update 2026-10-05 - saves U03, U04, U05 and the national-idea analysis

Status: the results below come from one run each of the scripts `backend/scripts/research/u345_ships_*.py`, `u345_f_*.py` and `u345_chain_*.py`. Unlike the Verification section above they have not been re-computed by an independent verifier. Labels: `confirmed` = whole set with exceptions listed, `inferred` = otherwise.

New data: U03 (1691.1.9), U04 (in-game date 1691.11.1, a tick day; its file name says 11.17) and U05 (1693.4.15) are melted Ironman saves of the same Ottoman campaign as S79 (1665.4.22) and S80 (1682.4.18); they add 323 entries with `light_ship`, all 538 entries of the five saves now fit [second pass 2026-10-05: 539 entries, all fit; see the end of this section]. They are not independent of S79/S80.

### U-1 What sets `f` (updates Q3)
- Values over the 538 entries of S79, S80, U03, U04, U05: f = 1.0 in 523, 1.1 in 12, 1.2 in 2, 1.05 in 1 [second pass: 539 entries, f = 1.0 in 524 - the S80 SPA malacca entry that was left out as ambiguous has f = 1.0 under both candidate fleet subsets]; never below 1; TUR itself has f = 1.0 in all 28 of its entries.
- **"Lucky nations" is rejected** (confirmed): the save stores the setting as `luck=yes` in `countries.<TAG>` (S79: BRA, FRA, GBR, HAB, POL, POR, RUS, SPA; S80 and U03-U05 also BRZ [second pass: in S80 and U03-U05 the list is BRA, BRZ, FRA, GBR, HAB, POL, RUS, SPA, i.e. BRZ is added and POR is no longer lucky]). None of the 6 countries below is lucky; the 30 lucky (save, country) pairs all have f = 1.
- **Leaderless fleets: the national idea set decides** (confirmed as an association, 0 exceptions in 332 leaderless (save, country) pairs; f is constant per country in 332 of 332). Ten (save, country) pairs have f != 1, all with one of three national idea groups in `active_idea_groups`, and these groups occur in no pair with f = 1:

| Country | Saves | Node | f | National idea group |
|---|---|---|---|---|
| LAI, VIL, VNL | S79, S80 | polynesia_node | 1.1 | `fijian_ideas` (6 pairs, all 1.1) |
| MNA, TDO | S79 | philippines | 1.1 | `luzon_ideas` (2 pairs, both 1.1) |
| SAM | S79, S80 | polynesia_node | 1.2 | `samoan_ideas` (2 pairs, both 1.2) |

  All other national sets have f = 1 in every leaderless pair (e.g. `hawaiian_ideas` 20 pairs, `chinese_ideas` 10, `swahili_ideas` 8, `maori_ideas` 3, about 50 further tag sets), and generic groups do not separate (`defensive_ideas` 7: 10 pairs with f != 1 and 182 with f = 1). The node does not decide (`polynesia_node` has 28 entries with f = 1: HAW, KAA, MAU, OAH, TAK, TEA, TOG, WAI, C22), and no numeric country field or sub-block separates the six from the 72 ship owners at f = 1. That the mechanism is a ship trade-power bonus in those three idea sets (10% Fijian and Luzon, 20% Samoan) is **inferred**: the idea definitions are not in the saves.
- **Leader fleets: `maneuver` fits** (inferred): the 5 entries whose protect fleet has a `leader` all have f != 1 (DAN lubeck 1.1, SPA ivory_coast 1.05, HOL english_channel 1.1 in U03, U04, U05); the leaders' `maneuver` is 2, 1, 2, and f = 1 + 0.05 x maneuver fits 3 of 3 distinct leaders, while fire (3, 1, 3), siege (2, 1, 0) and shock (3, 0, 0) do not [second pass: the fire values are (0, 1, 3) for (DAN, SPA, HOL) - (3, 1, 3) was a transcription error; siege (2, 1, 0) and shock (3, 0, 0) are right; fire, siege and shock still do not fit]. This explains why DAN (1.0 at north_sea, st_lawrence) and SPA (1.0 at malacca, genua, sevilla) differ by node: only the entry with a leader fleet is raised. Open: no leader with maneuver 0 or >= 3, no entry with a leader and an own-idea bonus together (so add vs multiply is UNKNOWN), no entry with a leader fleet and other fleets.
- Consequences for Q3's "rejected" list: (a) a leader in the fleet is **not** rejected (the 5 leader entries all have f != 1; the 10 leaderless entries are explained by the idea sets); (d) a per-country constant is right for leaderless fleets.

### U-2 `ship_power` is inside `max_pow`; marginal ship (updates Q6)
- `max_pow = province_power + ship_power + prev + 5 x has_capital + sum(modifier.power) + R` with coefficient exactly 1 on `ship_power` (R = the country's merchant constant of R06): the residual equals R within 0.0025 in 476 of 476 entries with ships (S79 92, S80 90, U03 94, U04 100, U05 100); the alternative "ship_power not in max_pow" fits 0 of 476 (confirmed).
- In the 19 entry pairs where only the ships changed (same `province_power`, `prev`, capital flag, modifier powers, merchant flag, transfers), `d(max_pow) = d(ship_power)` in 19 of 19 and `d(val) = d(max_pow x max_demand)` in 19 of 19, at steering, collecting and passive entries. Example: TUR hormuz, where TUR takes no merchant action, 0 to 11 ships between U03 and U04: ship_power +38.5, val 463.095 to 548.411. TUR basra (steering): 0 to 5 ships, +17.5 ship_power, val 334.494 to 373.274 (= 17.5 x 2.216).
- `max_demand` drifts between saves (unchanged within 0.0015 in only 6 of the 19 pairs), so the val change per ship is `f x base_T x max_demand` only for the current `max_demand`.

### U-3 Money per ship is indirect (answers the open part of Q6)
- The ship power enters the node's power pools exactly: the recorded change of `pull_power` or `retain_power` equals TUR's own change in effective power [second pass: it equals the change of ALL countries counted in that pool; TUR's own change alone matches only where no other country changed - see the second-pass subsection] (hormuz +85.382 recorded vs +85.316 own; basra +38.992 vs +38.780; the_moluccas -125.801 vs -125.801). TUR at hormuz counts as pulling because it collects downstream (R03 rule).
- Money appears only at nodes where the country collects. A replay through the project's green stages with the recorded steering weights held fixed gives about +0.1 to +0.4 ducats per month per frigate at a collecting node, about +0.004 to +0.25 per frigate at a pulling node (showing up at the downstream collecting nodes), and exactly 0 where no TUR collector lies downstream (S79 genua, 20 ships) (inferred: a model result, not a recorded one).
- The recorded money changes between the saves are confounded by other changes: comorin_cape (64 to 8 ships) is explained by ships for -15.0 of the recorded -15.6; at constantinople the ship part is +2.97 and +1.67 against upstream income changes of +3.6 and -12.7 and trade-efficiency changes of +3.4. No collecting entry with a ships-only change has an otherwise unchanged node, so a recorded per-ship income effect does not exist in the corpus.

### U-4 Uncounted fleets (updates Q4)
- All 565 counted protect fleets in the five saves have `on_my_way = no` [second pass: 566 unambiguously counted fleets, plus one of the two fleets of the undecidable S80 SPA malacca group]; of the 16 uncounted fleets 12 lack the key and 4 have it (all four in S79: C03 "1st Fleet" and "9th Fleet", TUR "Kizildeniz", "Karadeniz"). In U03-U05 no uncounted fleet has the key (0 counterexamples among 340 fleets [second pass: 342 fleets in U03-U05, 340 counted and 2 uncounted]). One fleet was followed by id: BNG "1st Fleet" (id 403526) at hangzhou lacks the key and is uncounted in U03, and has `on_my_way = no` and is counted in U04 and U05 (inferred: counted only once it has the key; meaning of the key UNKNOWN).
- No per-node cap below the observed maximum: GBR english_channel 77 ships (U04, U05).
- TUR passive at hormuz with 11 frigates: ships give `max_pow` and `val` at a node without a merchant action.

### Verification 2026-10-05 (second pass)

Independent code (new, not reusing the authors' logic): `backend/scripts/research/ver2_r11_a.py` (fleet/entry reconciliation and f over all 85 saves, with no prior on the value of f), `ver2_r11_b.py` and `ver2_r11_b2.py` (idea groups, luck, leader stats), `ver2_r11_c.py` and `ver2_r11_c2.py` (max_pow residual, ships-only pairs), `ver2_r11_d.py` (retain/pull pools), `ver2_r11_e.py` (counted/uncounted fleets), `ver2_r11_f.py` (lucky tags, per-save residuals, closed-form money model). Only S79, S80, U03, U04, U05 contain `light_ship` entries; U01/U02 are copies of S80/S79 and are not counted twice.

Matched (re-computed, same numbers):
- Fleet reconciliation: every one of the 539 entries fits a subset of the protect fleets by ship count alone (S79 112, S80 104, U03 104, U04 109, U05 110; 323 new); f histogram 1.1 in 12, 1.2 in 2, 1.05 in 1 (see corrections for 1.0); TUR 28 entries, all f = 1.0 (6, 3, 4, 7, 8).
- National idea groups: `fijian_ideas` 6 pairs all 1.1, `luzon_ideas` 2 pairs 1.1, `samoan_ideas` 2 pairs 1.2; these groups occur in no pair with f = 1; all 10 leaderless pairs with f != 1 carry one of them; among the 332 (save, country) pairs without any leader entry f is constant per country; `hawaiian_ideas` 20, `chinese_ideas` 10, `swahili_ideas` 8, `maori_ideas` 3 pairs all f = 1; 60 of 63 idea groups seen in at most three countries occur only with f = 1 (the other 3 are the three groups above); `defensive_ideas` 10 pairs with f != 1, 182 with f = 1.
- Lucky nations: 30 of the 332 pairs are lucky, all f = 1; 0 lucky pairs with f != 1; none of the six is lucky.
- Leader: 5 entries with a leader fleet (DAN lubeck 1.1, SPA ivory_coast 1.05, HOL english_channel 1.1 x3); maneuver 2, 1, 2; (f-1)/maneuver = 0.05 for all; fire, siege, shock do not give a constant ratio (each has a zero stat where f != 1 or two different ratios).
- `max_pow` residual: 476 of 476 entries with ships equal R within 0.0025 when R is the modal residual of the same country's ship-less entries with the same merchant presence (S79 92, S80 90, U03 94, U04 100, U05 100); the alternative fits 0. With the finer class (merchant presence, steering, collecting) the test covers 247 entries, 247 of 247, alternative 0.
- Ships-only pairs: 19 (S79->S80 3, U03->U04 8, U04->U05 3, U03->U05 5) = 9 steering, 9 collecting, 1 passive; d(max_pow) = d(ship_power) in 19 of 19; val = max_pow x max_demand in 19 of 19; max_demand unchanged in 6 of 19; TUR hormuz 0 -> 11 ships: ship_power +38.5, val 463.095 -> 548.411; TUR basra 0 -> 5: +17.5, val 334.494 -> 373.274 (max_demand 2.216).
- Largest entries: GBR english_channel 77 ships (U04, U05), TUR the_moluccas 70 (U03) and 65 (S80).
- Uncounted fleets: U03 1 (BNG 1st Fleet, hangzhou), U04 1 (DEC 6th Fleet, ganges_delta), U05 0; the four S79 uncounted fleets with `on_my_way = no`: C03 1st and 9th Fleet (mexico), TUR Kizildeniz (comorin_cape) and Karadeniz (gulf_of_aden); BNG fleet id 403526: uncounted without the key in U03, counted with `on_my_way = no` in U04 and U05.
- Pool identity (part): the project's R03 rule reproduces the recorded retain/pull in 79-80 of 80 nodes per save; TUR at hormuz counts as pulling (passive, collects downstream).
- Zero effect of TUR's 20 ships at S79 genua: genua is an end node (no downstream node) and TUR neither collects nor steers there, so the ships are in no pool.

Corrected (old -> new, why):
- Entries: 538 -> 539, f = 1.0: 523 -> 524. The S80 SPA malacca entry (5 ships, 16.5) has two candidate fleet subsets ({12th Fleet, Flota de Mariana Islands} or {Flota de Mariana Islands, 3rd Fleet}); both give f = 1.0, so it belongs in the histogram.
- Lucky tags: "S80 and U03-U05 also BRZ" -> in S80 and U03-U05 the lucky tags are BRA, BRZ, FRA, GBR, HAB, POL, RUS, SPA (POR is dropped).
- Fire values of the three leaders: (3, 1, 3) -> (0, 1, 3) for (DAN, SPA, HOL). The conclusion (only maneuver fits) is unchanged.
- Pool change: "equals TUR's own change" -> equals the summed change of all countries counted in the pool under the R03 rule, residual 0.000 in 10 of 10 same-pool rows. TUR alone matches exactly only where no other country changed (the_moluccas -125.801 and +16.601, where others change by 0.000). Differences otherwise are other countries: hormuz others +0.066, basra +0.212, gulf_of_aden +1.597 (recorded +32.513 vs +30.916), malacca +0.915 (recorded +11.848 vs +10.933), philippines U04->U05 +7.360 (recorded +90.628 vs +83.268), gujarat +19.817 (recorded +36.311 vs +16.494), comorin_cape +22.857.
- Fleet counts: 565 counted -> 566 unambiguously counted fleets (all with `on_my_way = no`), 16 unambiguously uncounted (12 without the key, 4 with `no`), 2 fleets undecidable by the data (S80 SPA malacca: "12th Fleet" with `no` and "3rd Fleet" without the key, one of them is counted; the earlier resolution 'the one without the key is the uncounted one' assumes the rule being tested). U03-U05: 342 fleets (340 counted, 2 uncounted), not 340.
- Per-frigate money at a collecting node: recomputed in closed form from recorded retain/pull/current/money (gross x eff / (retain + pull) x money/share, others held fixed; reproduces the recorded money of the_moluccas U04 exactly, 54.957): one more frigate adds +0.16 (the_moluccas U04), +0.34 (comorin_cape U04), +0.22 (gujarat U04), +0.40 (comorin_cape U05) ducats; removing the whole fleet gives -7.3 (35 ships), -1.9 (8), -2.9 (14). This agrees with the stated range '+0.1 to +0.4'; the exact figures of the staged analysis for single frigates (0.131, 0.337, 0.196, 0.386) differ slightly (the_moluccas 0.131 vs 0.160, gujarat 0.196 vs 0.218).

Additional fact found: HOL english_channel has f = 1.0 in S79 and S80 (no leader in the counted fleets) and f = 1.1 in U03, U04, U05 (leader with maneuver 2 in the counted fleet): same country and node, f changes with the leader (supports the leader cause and a per-fleet, not per-country, effect).

Unverifiable by this pass: the pulling-node per-frigate range (+0.004 to +0.25) and the effect of ships on downstream flows (needs a full replay through link flow; the steering weights rule R08 is unknown); the mechanism (modifier names and values) of the national idea sets and of the leader effect (no game files in the saves); the meaning of `on_my_way`.

## Update 2026-10-05 - Venice series U07-U30 (new game, VEN, 1444.11.11 to 1445.07.02)

Status: scripts `backend/scripts/research/venice_c_ships.py`, `venice_c_fleet_lag.py`, `venice_c_shipdelta.py`, `venice_c_x_home.py`, `venice_c_ver3.py` (F), `venice_c_ver6.py`; loader `venice_load.py`, independent regex readers `venice_c_raw.py`. First ship data outside the TUR campaign and the first with a single known fleet: VEN's "2nd Fleet" (3 barques, no leader) plus an unassigned "1st Fleet" (9 galleys, 13 cogs). The player changed the 2nd Fleet's protect mission twice between saves; everything else about the fleet was left alone.

### VH-1 `f` = 1 and `ship_power` is inside `max_pow` with coefficient 1, in a clean single-fleet case (confirms U-1, U-2)
Claim: 3 barques give `ship_power 6.0` = 3 x 2.0 (`barque` trade_power 2.0 in `light_ships.json`), i.e. f = 1.0, when the country has no national idea unlocked (`active_idea_groups = {VEN_ideas: 0}`) and the fleet has no leader; the term is additive in `max_pow` with coefficient 1: at the four node-pairs of the two fleet moves the change of `max_pow` equals the change of `ship_power` plus the change of `province_power` plus the change of `prev` with residual 0.000.
Source: `venice_c_shipdelta.py`, independent `venice_c_ver6.py`.
Quote: `venice` 1445.1.31 -> 2.1: max_pow 110.637 -> 104.681 (-5.956 = -6.000 + 0.044); `ragusa` 1.31 -> 2.1: 46.482 -> 52.520 (+6.038 = +6.000 + 0.029 + 0.009); `ragusa` 2.28 -> 3.1: 52.520 -> 46.539 (-5.981 = -6.000 + 0.014 + 0.005); `alexandria` 2.28 -> 3.1: 21.936 -> 27.941 (+6.005 = +6.000 + 0.005). `val` = `max_pow` x `max_demand`: venice 110.637 x 1.323 = 146.37, 104.681 x 1.323 = 138.49.
Confidence: confirmed (4 of 4 node-pairs; f = 1 only for this case: national idea sets and leaders are not varied here).
Also: the other fleet (9 galleys + 13 cogs, no mission) adds nothing anywhere (no `light_ship` in any entry for it), as in C-02.

### VH-2 The ship term follows the mission with a lag to the next 1st; the field of the country does not lag
Claim: the node whose VEN entry carries `light_ship`/`ship_power` is the node of the fleet's `protect_mission.node` as it was at the last 1st, not the current mission node and not the fleet's position: the country field `num_ships_protecting_trade` changes at once.
Source: `venice_c_fleet_lag.py`, independent `venice_c_ver3.py` F.
Rows (mission node index: 79 venice, 59 ragusa, 47 alexandria): 1444.11.11 no mission, no ship entry, field absent; 11.14 mission 79, field 3, no ship entry; 11.30 same; 12.1 ship entry at venice; 1445.1.15 mission 79, entry venice; 1.24 mission 59 (ragusa), entry still venice (also 1.30, 1.31); 2.1 entry at ragusa; 2.3 mission 59, entry ragusa; 2.10 mission 47 (alexandria), entry still ragusa (2.17, 2.28); 3.1 entry at alexandria (3.31 to 7.2 unchanged). The fleet is at sea on a patrol route while this happens (`location` 1312, 1932, 1319, 1313-1315 ...): the entry is at the mission node even when the fleet is elsewhere.
Confidence: confirmed (3 of 3 mission events: assignment, two changes).
Consequence for the calculation: the ship term of a what-if change of a mission appears after the next 1st; a save taken between two 1sts shows the previous assignment.

### VH-3 `on_my_way` is false for a counted fleet, also while it moves
Claim: `protect_mission.on_my_way = no` in every save from 11.14 to 7.2 (23 of 23), including saves where the fleet is sailing to a new mission node (1445.1.24 - 2.3, 2.10 - 2.28), and the fleet is counted. So `on_my_way = no` is not what excludes the four S79 fleets of U-4 (`on_my_way` meaning: still UNKNOWN; these four stay unexplained).
Source: `venice_c_fleet_lag.py`. Confidence: confirmed as an observation.

### VH-4 The ship on the collecting home node: `total` moves by about -1%, efficiency does not move with it
Claim: VEN collects at `venice` (home) without a merchant. The ship term sat at `venice` from 12.1 to 1.31 (not before: 11.11-11.30 the mission existed but the entry did not), and left on 2.1: VEN's `total` there 5.689 (1.31) -> 5.634 (2.1), `power_fraction` 0.603 -> 0.591; `money/total` was 1.1200 with no ship term (11.11-11.30), 1.1199 with it (12.1-1.31) and 1.1699 without it again (2.1 on). So the ship term does not change the efficiency X at the collecting node (X equal with and without the term), and the +0.05 step of X at 2.1 is not caused by the ship leaving (it was 1.12 in the ship-less snapshots before).
Caveat: every country's values change at a 1st, so the change of `total` is not an isolated ship effect (inferred: the drop is the ship's 6.0 of 110.6 power = 5.4% diluted by the node's other power).
Source: `venice_c_x_home.py`. Confidence: confirmed (observation); the cause of the X step is UNKNOWN (R07).

### Verification 2026-10-05 (second pass, Venice series)
VH-1: the four residuals recomputed with the regex readers (`venice_c_ver6.py`): identical. VH-2: mission node and entry location read from the raw text (`venice_c_ver3.py` F): identical for all 24 saves. VH-3 and VH-4 computed once (parsed; the X values for the 24 saves are also in `venice_c_ver3.py` C, identical).

## Data basis (2026-10-06)

On 2026-10-06 the research data was rebuilt (`docs/research/data_audit.md`): only **clean** saves are kept (the 1st of a month after the game's first trade computation, none of the player's merchants or fleets on the way; R12 final). Kept: U04 (TUR 1691.11.01), U10, U14, U20, U25, U27, U28, U29 (VEN 1444-1445). Removed: the 78 start snapshots S01-S78 and U07-U09 (saved before the first computation: steering weights, `add` and other computed fields are placeholders there) and 21 mid-month saves (S79, S80, U01-U03, U05, U06, U11-U13, U15-U19, U21-U24, U26, U30: numbers from the last 1st, merchant/ship flags from the save day). Counts above that include removed saves are kept as recorded but are **unverified on clean data** unless listed as re-checked below. Clean-data stage results quoted here: `scripts/verify_all.sh` on the 8 kept saves (calc 0.2.0).

- All ship evidence came from S79, S80, U03-U06; only U04 is kept (clean). Ship counting compares the save day's fleets (`on_my_way`) with the 1st's `light_ship`/`ship_power`: mid-month saves can mismatch by construction. Re-verify on U04 and the ship experiments (`exp-core-1444` B6-B10).


## Update 2026-10-07 - controlled experiments (E00-P06)

Source: single-change experiments run in the game (EU4 1.37.5) with the automation in `tools/EU4-game-automation/experiments/` (`PLAN.md`, `RESULTS.md`, scripts `analysis/a1`-`a8`). Every treatment loads the same base save `out/E00/base_1444.12.01.eu4` (new game VEN 1444.11.11, spectator mode, saved on the first tick day), applies one change on 1444.12.01, runs with the AI of VEN switched off and is saved on 1445.01.01 (t1, first tick with the change) and 1445.02.01 (t2); saves under `tools/EU4-game-automation/experiments/out/<id>/` (67 saves checked: date, player VEN, plain text). Noise (controls E01a-E01d): two runs from one save diverge in other countries' fields (E01a vs E01b: 4,859 of 73,073 trade-block fields at t1, 8,029 at t2), but 101 of 103 VEN entry fields are identical in all four controls; only venice `money`/`total` vary (about +-0.6 %). Single-run comparisons are therefore used only for VEN power, demand, `val`, `prev`, `province_power`, `ship_power`, `add` and merchant fields, and for income only as the ratio `money/total`.

### V2-R11-1 `global_ship_trade_power` scales ship power; ships enter `max_pow` 1:1
Claim (E07): +50 % `global_ship_trade_power` raises VEN `ship_power` at venice 4.000 -> 6.000 and `max_pow` +2.000 (2 light ships on a protect-trade mission at venice). Confidence: confirmed.

### V2-R11-2 Moving one fleet
Claim (P05): VEN's light-ship fleet moved by a save patch from venice to ragusa: `ship_power` 4.000 and `light_ship` 2 move from venice to ragusa, `max_pow` -4.000 / +4.000, no upstream `prev` change. This is the one-assignment pair asked for; its income ratio (`money/total` at the collecting home node) has not been extracted yet. Confidence: confirmed (power fields).

## Update 2026-10-08 - experiment round 2

Source: 27 single-change jobs run in the game by the automation (`tools/EU4-game-automation/experiments/round2/`: `PLAN.md`, `RESULTS.md`, scripts `analysis/`); saves under `round2/out/<id>/` (t1 = 1445.1.1, t2 = 1445.2.1; all dated, player and plain text checked). Controls as in round 1 (E01c / E01d on the E00 base) plus R2-C-U10, R2-H-MAM-C, R2-H-TUR-C, R2-C-NED18. **Void:** every merchant recall by save patch (R2-B5a, R2-B4, R2-B5c, R2-H-MAM-B1, R2-H-TUR-B1 and the recall half of R2-B5b / R2-H-MAM-B2): the patched save has no merchant at the node, t1 has it again (cause unknown); the embargo (R2-EMB) and privateer (R2-PRIV) patches are dropped on load; R2-TC added nothing (no territory province). No claim below rests on a recall.

### V4-R11-1 Ship power moves 1:1 with the fleet; income effect of one fleet
Claim (R2-SHIPCON): 2 barques (2.0 each, `common/units`) moved from VEN's home node to constantinople: `ship_power` 4.000 / `max_pow` +4.000 there, -4.000 at venice, no `prev` change; VEN home `total` -0.8 % (5.307 -> 5.264). Per-type values (frigates etc.) still need later-era saves. Confidence: confirmed.
