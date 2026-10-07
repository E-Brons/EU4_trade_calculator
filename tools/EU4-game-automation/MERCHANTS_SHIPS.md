# Merchants and light ships: how a job can place them (EU4 1.37.5)

Research 2026-10-06, offline (game files + Venice series saves in `datasets/eu4/1.37.5/vanilla/dlc-819b35e6/venice-1444/`).
Patch code: `savepatch.py`. Nothing here has been loaded into the game yet.

## 1. Game-side routes (no UI)

| Need | Console (`commands_1.37.5.md`) | Effect usable via `run <file>` | Verdict |
|---|---|---|---|
| send / recall a merchant, choose collect / steer | none | none: vanilla scripts only read merchants (`has_merchant`, `num_of_merchants`, `trade_steering`, `placed_merchant_power`) or change their count (`merchants` modifier) | not possible |
| trade power in a node without a merchant | - | `add_trade_modifier = { who = root duration = 7300 power = 5 key = control_of_famagusta }` (events/FlavorVEN.txt:93, province scope = that province's node) | possible, but it is a modifier, not a merchant |
| create light ships | `spawn [province] [unit]` (untested), `flagship_light` | `add_unit_construction = { type = light_ship amount = 2 speed = 0.5 cost = 0 }` (events/TradeLeague.txt:159, builds over time); `build_to_forcelimit = { light_ship = 0.3 ... }` (events/flavorDAN.txt:2194, province scope) | ships: yes |
| put a fleet on "protect trade" in a node | none | none (no mission effect in vanilla) | not possible |

So merchant placement and fleet missions need either save patching (below) or UI clicks (merchant: trade view ->
node -> send merchant -> collect/steer + direction; fleet: select fleet -> mission button -> protect trade -> node).

## 2. Save structure (evidence)

Merchant, node entry `trade.node[definitions=N].<TAG>`:
- stationed merchant: `has_trader=yes` (both roles).
- steering: `type=1` plus `steer_power=<i>`, `i` = 0-based index of the target in the node's outgoing list in
  `common/tradenodes/00_tradenodes.txt` (same order as `backend/data/tradenodes.json`, 80/80 nodes); the key is
  omitted for `i = 0`. U25 VEN: ragusa `[pest, venice, genua]` -> `steer_power=1`; alexandria
  `[constantinople, venice, genua]` -> `1`; wien `[venice, rheinland, saxony]` -> no key.
- collecting: `has_trader=yes` without `type` / `steer_power` (516 such entries in U25).
- recall (U25 -> U27 ragusa): `has_trader` and `type` removed, `steer_power=1` stays; `add`, the merchant term of
  `max_pow` (46.539 -> 44.565) and weights follow on the next 1st (R12 C-05). No modifier is added for a player
  recall (AI recalls get `merchant_recalled`, R06).

Merchant, country `countries.<TAG>`:
- `merchants={ envoy={ action=2 name=.. type=1 id=.. } ... }`: `action=2` = stationed. The envoy has no node field.
  Count of `action=2` envoys == count of `has_trader` entries in 663/663 countries (U25). U27 (0 merchants): no
  `action`; U28 (ragusa re-sent): one `action=2`.
- `transfer_home_bonus` = 0.1 x steering merchants: U25 0.300 (3), U27 0.000, U28 0.100 (R09).

Light ships:
- country: navy `{ ... location=<sea> ... ship={ type="barque" ... } ... mission={ protect_mission={ retreat_port=3003
  was_safe_retreat_port=yes node=47 trade=1313 trade=1314 ... current_route_target=4 current_cycle_begin=1
  on_my_way=no } } movement_locked=yes ... }` (U25 VEN navy 234, 3 barques). `node` = 1-based position of the node in
  the save's `trade.node` list (47 = alexandria). `trade=` = patrol sea zones chosen by the game (not the node's
  `members`, which are land provinces).
- node entry: `light_ship=3`, `ship_power=6.000`; country `num_ships_protecting_trade=3`. Light ships of a tag's
  fleets on missions in node k == entry `light_ship` in 226/227 pairs (U25; the exception is ORM gulf_of_aden).
- light-ship unit types (`common/units`, `type = light_ship`): barque, caravel, early_frigate, frigate, great_frigate,
  heavy_frigate.

## 3. What `savepatch.py` does

| Function | Edits | Basis |
|---|---|---|
| `place_merchant(text, tag, node, "steer"/"collect", direction)` | entry: `has_trader`, `type`, `steer_power`; one free envoy `action=2`; `transfer_home_bonus` | evidence; offline round trip U27 + place ragusa = U25/U28 fields, only 5 lines differ |
| `recall_merchant(text, tag, node)` | entry: drop `has_trader`, `type`; one envoy loses `action=2`; `transfer_home_bonus` | evidence; round trip U25 - recall = U27 fields |
| `set_light_ship_mission(text, tag, node, navy_id=None)` | the tag's light-ship-only (or given) navy: new `protect_mission` with `node=<index>`, route copied from a fleet already protecting that node, `location` = first route zone, `path`/`movement_progress` dropped | structure from evidence; route copy and teleport are GUESSES |

Derived values are not recomputed: load the patched save and run to the next 1st before saving (R12).

## 4. Untested

- Whether the game accepts each patch on load (and keeps it through the first tick), especially: a new node entry for
  a tag that had none; the fleet teleport / copied route; mission block position inside the navy (moved to the end).
- A node no fleet protects in the save: no route to copy -> the patch refuses.
- Merchants in transit (no evidence: only 1st-of-month saves are stored).
