# R05 - Trade power propagation between nodes (the prev field)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R05_trade_power_propagation_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R05_trade_power_propagation_draft.md`

```
# R05 results - Trade power propagation between nodes (the prev field)
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

Define the exact rule for `prev` (power propagated into a node), including direction, divisor, threshold, which power types propagate, how links are split, and what modifiers apply (`ship_power_propagation`, `caravan_power`, trade steering...).

Our fit on the real save: **`prev_B(country) = sum over the nodes D that B sends value to (B's outgoing links; i.e. D downstream of B) of province_power_D(country) / 5`** (`TRADE_PROPAGATE_DIVIDER = 5`); ship power does not propagate (fitted ship coefficient 0.000); the chained `prev` of D does not propagate either. It reproduces 493 of 519 entries within 1% (median error 0). We do not know the threshold rule (`TRADE_PROPAGATE_THRESHOLD = 2`: on which quantity, applied before or after dividing?), what the 26 failing entries have in common, or whether it is `province_power` or something close to it (e.g. province power after some modifier, or power including capital/merchant extras).

Questions: (1) confirm direction (power flows from downstream nodes back upstream? or the opposite from the node's own perspective) and quote; (2) exact threshold semantics; (3) does the divisor depend on the number of links or on distance; (4) do collecting/steering merchants or capital extras propagate; (5) role of `ship_power_propagation` (country modifier, base 0?) so ships may propagate when it is positive; (6) does `caravan_power` add power in nodes where it propagates; (7) rounding/ordering effects.

## Failing entries (`prev` vs `sum(province_power_D)/5`), real save, first 22 of 26

`D` = downstream node (outgoing link target of the node), values are that country's raw parts at D.

| node B | country | prev (save) | prediction | downstream D: parts |
|---|---|---|---|---|
| patagonia | C06 | 19.9 | 20.889 | laplata: prov 4.94 ship 0.00 prev 2.45; cuiaba: prov 99.50 ship 0.00 prev 29.33 |
| california | POR | 2.04 | 2.164 | mexico: prov 0.00 ship 0.00 prev 2.04; mississippi_river: prov 0.62 ship 0.00 prev 0.00; polynesia_node: prov 10.20 ship 0.00 prev 0.00 |
| mississippi_river | C04 | 2.719 | 4.675 | carribean_trade: prov 13.60 ship 27.50 prev 16.68; ohio: prov 9.78 ship 0.00 prev 16.68 |
| chengdu | MNG | 11.318 | 12.777 | canton: prov 56.59 ship 0.00 prev 24.60; xian: prov 5.83 ship 0.00 prev 0.00; burma: prov 1.46 ship 0.00 prev 6.51 |
| chengdu | BNG | 59.124 | 60.055 | canton: prov 113.20 ship 0.00 prev 0.00; xian: prov 4.65 ship 0.00 prev 0.00; burma: prov 182.42 ship 0.00 prev 76.63 |
| gulf_of_siam | KHM | 4.544 | 5.458 | malacca: prov 22.72 ship 7.50 prev 0.00; canton: prov 4.57 ship 0.00 prev 4.54 |
| canton | TUR | 13.33 | 14.632 | malacca: prov 66.65 ship 74.00 prev 0.00; hangzhou: prov 0.00 ship 0.00 prev 13.33; philippines: prov 6.51 ship 0.00 prev 19.49 |
| canton | BEI | 14.429 | 14.909 | malacca: prov 72.15 ship 24.00 prev 0.00; hangzhou: prov 0.00 ship 0.00 prev 14.43; philippines: prov 2.40 ship 0.00 prev 0.00 |
| philippines | TUR | 19.491 | 19.743 | the_moluccas: prov 97.45 ship 0.00 prev 13.33; polynesia_node: prov 1.26 ship 0.00 prev 0.00 |
| cuiaba | C06 | 29.33 | 30.319 | laplata: prov 4.94 ship 0.00 prev 2.45; lima: prov 134.38 ship 29.00 prev 0.00; brazil: prov 12.27 ship 7.00 prev 0.00 |
| xian | CSH | 17.609 | 19.482 | beijing: prov 88.05 ship 5.00 prev 0.00; yumen: prov 9.36 ship 0.00 prev 0.00 |
| deccan | TUR | 3.968 | 4.58 | gujarat: prov 19.84 ship 0.00 prev 38.67; comorin_cape: prov 3.06 ship 45.50 prev 9.70 |
| gujarat | AJU | 14.849 | 15.258 | gulf_of_aden: prov 74.25 ship 66.00 prev 0.00; zanzibar: prov 2.04 ship 0.00 prev 0.00 |
| katsina | SPA | 12.012 | 12.675 | timbuktu: prov 3.31 ship 0.00 prev 23.83; tunis: prov 60.06 ship 0.00 prev 121.59 |
| gulf_of_aden | SPA | 2.662 | 4.3 | zanzibar: prov 13.31 ship 0.00 prev 4.26; alexandria: prov 8.19 ship 0.00 prev 20.75 |
| basra | IRQ | 9.175 | 9.405 | aleppo: prov 45.88 ship 0.00 prev 0.00; persia: prov 1.14 ship 0.00 prev 9.18 |
| alexandria | SPA | 20.755 | 21.886 | venice: prov 5.66 ship 0.00 prev 0.00; genua: prov 103.78 ship 10.00 prev 0.00 |
| alexandria | BLG | 7.285 | 9.001 | venice: prov 36.43 ship 10.50 prev 0.00; genua: prov 8.58 ship 0.00 prev 0.00 |
| novgorod | DAN | 15.125 | 15.339 | baltic_sea: prov 75.63 ship 0.00 prev 47.69; white_sea: prov 1.07 ship 0.00 prev 14.15 |
| ivory_coast | SPA | 88.069 | 89.203 | carribean_trade: prov 0.00 ship 0.00 prev 77.28; bordeaux: prov 5.66 ship 0.00 prev 0.00; english_channel: prov 53.95 ship 0.00 prev 0.00; sevilla: prov 386.40 ship 139.00 prev 23.56 |
| ragusa | SPA | 20.755 | 21.886 | venice: prov 5.66 ship 0.00 prev 0.00; genua: prov 103.78 ship 10.00 prev 0.00 |
| ragusa | BLG | 7.285 | 9.001 | venice: prov 36.43 ship 10.50 prev 0.00; genua: prov 8.58 ship 0.00 prev 0.00 |
