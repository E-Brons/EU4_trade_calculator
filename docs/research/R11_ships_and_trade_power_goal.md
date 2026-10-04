# R11 - How assigned light ships become trade power in a node

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R11_ships_and_trade_power_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R11_ships_and_trade_power_draft.md`

```
# R11 results - How assigned light ships become trade power in a node
## 1. Answer
(the rule and exact formula as pseudo-code; inputs named by their save field or game define)
## 2. Variables
(a JSON array; one object per variable: {"id","meaning","unit","kind":"constant|read|derived|unknown","source":{"type":"defines.lua|save|script|other","path":"..."},"confidence"})
## 3. Claims
### C-01 <short name>
Claim: ...
Formula: ...
Applies when: ...
Source: <URL or file:line>
Quote: "<verbatim>"
Confidence: confirmed|reported|inferred
Caveats / contradicts: ...
## 4. Validation against the data in this task
(per row or group: reproduced or not, with arithmetic; list every failure)
## 5. Unknowns, contradictions between sources, and what would settle them
## 6. Sources (ranked, one line on reliability each)
```

---
## Question

Define exactly how light ships convert to `ship_power` at a trade node and what limits them: per-type `trade_power` (`common/units`: barque 2.0, caravel 2.5, early_frigate 3.0, frigate 3.5, heavy_frigate 4.0, great_frigate 5.0), modifiers (`global_ship_trade_power`, `ship_trade_power_modifier` e.g. caravel +0.33 and VOC Indiamen +0.2 in `static_modifiers`, `trade_power_in_fleet_modifier` of flagships, `naval doctrines`), whether `ship_power` already includes them, whether ships in port/at sea or low organisation count (`TRADE_SHIP_MAX_DAYS_IN_PORT = 5.0`, `TRADE_SHIP_ORG_LIMIT = 0.5`), the role of `OPEN_SEA_MODIFIER = 1.7` / `COASTAL_MODIFIER = 1.0` (do open-sea nodes give ships extra power?), `num_ships_protecting_trade` (TUR: 98 vs 100 light ships owned), whether ships can be assigned to inland nodes (we see none), and **how the assignment of a fleet to a node is stored in the save** (we only see `light_ship` count and `ship_power` per country per node) and how it is chosen/changed in game ("protect trade" mission on a node, and the cap on ships per node). We need a rule to compute how much power one more ship adds in a given node for a given country.

Observed: `ship_power / light_ship` over all 112 ship-bearing country-node entries in the corpus: min 2.000, median 3.000, max 3.675. TUR fleet composition by type: {'galleon': 4, 'merchantman': 50, 'galiot': 30, 'galley': 4, 'early_frigate': 66, 'frigate': 34, 'carrack': 5, 'galleass': 20, 'war_galley': 1}.

## TUR ship-bearing nodes (real save)

| node | tag | ships | ship_power | power per ship | province | prev | max_pow | max_demand | coast | role |
|---|---|---|---|---|---|---|---|---|---|---|
| malacca | TUR | 24 | 74 | 3.083 | 66.651 | 0 | 140.651 | 2.03 | coastal | passive |
| comorin_cape | TUR | 13 | 45.5 | 3.5 | 3.06 | 9.7 | 65.26 | 1.53 | coastal | steer |
| basra | TUR | 4 | 14 | 3.5 | 77.392 | 35.7 | 144.092 | 1.882 | coastal | steer |
| crimea | TUR | 1 | 3 | 3 | 52.312 | 75.423 | 147.735 | 1.648 | coastal | steer |
| genua | TUR | 20 | 63.5 | 3.175 | 18.24 | 0 | 81.74 | 2.11 | coastal | passive |
| venice | TUR | 36 | 110.5 | 3.069 | 164.781 | 0 | 292.281 | 0.92 | coastal | collect-away |

Note `ship_power` of the 36 ships at venice is 110.5 (3.07 per ship) although frigate=3.5: find what produces 3.07 (mixed types? a modifier below 1? ships that are not at sea?). Also: do ships add power through `prev` (propagation) in neighbouring nodes? (We found they do not.)
