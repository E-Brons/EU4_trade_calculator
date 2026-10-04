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
