# R01 - What determines max_demand (the multiplier from raw power to effective power)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R01_power_multiplier_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R01_power_multiplier_draft.md`

```
# R01 results - What determines max_demand (the multiplier from raw power to effective power)
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

The save stores, per country per node, `max_pow` (raw power) and `max_demand`, and `val = max_pow * max_demand` exactly. `max_demand` is therefore the multiplier that turns raw trade power into the power the game uses for sharing value. Explain **exactly how the game computes `max_demand`** for a country at a node: which country modifiers (`global_trade_power`, `global_own_trade_power` "Domestic Trade Power", `global_foreign_trade_power` "Trade Power Abroad", `trade_power` of trading policies, `global_prov_trade_power_modifier`, ...), which node properties, and which saturation/cap rules produce the values below.

Observations to explain: for the Ottomans (TUR) the multiplier equals **2.110 exactly at many nodes** (looks like a cap or a country-wide value), but is lower at some nodes (1.83, 1.718, 1.254, 1.098, 1.452...), and about half at nodes where TUR collects away from its capital (venice 0.92, ragusa 0.761; see R02 for the penalty). The other countries show country-specific caps (e.g. SPA 2.137, GEN 1.835 at alexandria, small countries 0.9-1.4). Is `max_demand = min(country_cap, f(node values))`? Is the cap = 1 + sum of some modifiers? What is the lower-than-cap rule (it is not explained by province/ship/prev shares)?

Also state how to **predict `max_demand` for a country at a node where it has no entry yet** (needed to evaluate placing a merchant or ships in a new node), and which of its inputs can be read from the save.

## Data: Ottoman Empire (TUR), 1665.4.22 save, every node where it has power

| node | role | province | ship | ships# | prev | max_pow | max_demand | val | node.total | node.max | node.p_pow | node.highest_power | node.num_collectors | trade_company_region |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gulf_of_siam | passive | 0 | 0 | 0 | 13.33 | 13.33 | 1.83 | 24.393 | 695.652 | 362.257 | 254.257 | 28.4 | 2 | yes |
| canton | passive | 0 | 0 | 0 | 13.33 | 13.33 | 1.718 | 22.9 | 683.437 | 375.175 | 245.175 | 75.762 | 3 | yes |
| philippines | passive | 6.51 | 0 | 0 | 19.491 | 26.001 | 2.11 | 54.862 | 424.033 | 237.721 | 139.121 | 25.984 | 5 | yes |
| polynesia_node | passive | 1.26 | 0 | 0 | 0 | 1.26 | 2.11 | 2.658 | 624.621 | 445.528 | 111.678 | 11.41 | 12 | yes |
| australia | passive | 0 | 0 | 0 | 19.491 | 19.491 | 2.11 | 41.126 | 445.245 | 252.23 | 198.73 | 27.185 | 1 | no |
| hangzhou | passive | 0 | 0 | 0 | 13.33 | 13.33 | 2.11 | 28.126 | 695.132 | 419.639 | 224.139 | 39.33 | 2 | yes |
| the_moluccas | passive | 97.455 | 0 | 0 | 13.33 | 110.785 | 2.11 | 233.756 | 587.263 | 307.732 | 223.232 | 30.72 | 1 | yes |
| malacca | passive | 66.651 | 74 | 24 | 0 | 140.651 | 2.03 | 285.521 | 1130.621 | 634.989 | 313.489 | 34.952 | 7 | yes |
| lahore | passive | 0 | 0 | 0 | 6.043 | 6.043 | 2.11 | 12.75 | 444.964 | 201.695 | 150.695 | 30.079 | 1 | yes |
| deccan | passive | 0 | 0 | 0 | 3.968 | 3.968 | 1.254 | 4.975 | 641.146 | 298.019 | 196.019 | 28.02 | 1 | yes |
| comorin_cape | steer | 3.06 | 45.5 | 13 | 9.7 | 65.26 | 1.53 | 99.847 | 944.51 | 622.487 | 367.987 | 37.259 | 2 | yes |
| gujarat | passive | 19.84 | 0 | 0 | 38.675 | 48.515 | 1.503 | 72.918 | 618.695 | 369.063 | 264.563 | 57.582 | 3 | yes |
| ethiopia | passive | 0 | 0 | 0 | 37.76 | 37.76 | 2.11 | 79.673 | 323.701 | 124.949 | 115.949 | 21.181 | 2 | yes |
| gulf_of_aden | steer | 28.66 | 0 | 0 | 64.971 | 110.631 | 2.11 | 233.431 | 918.916 | 445.046 | 226.546 | 30.66 | 5 | yes |
| hormuz | passive | 164.716 | 0 | 0 | 15.478 | 180.194 | 1.895 | 341.467 | 411.646 | 203.588 | 201.588 | 73.442 | - | yes |
| zanzibar | passive | 1.26 | 0 | 0 | 0 | 1.26 | 2.11 | 2.658 | 465.263 | 359.838 | 236.338 | 33.631 | 5 | yes |
| basra | steer | 77.392 | 14 | 4 | 35.7 | 144.092 | 1.882 | 271.181 | 467.948 | 199.67 | 131.67 | 28.48 | 2 | yes |
| samarkand | passive | 0 | 0 | 0 | 2.075 | 2.075 | 1.651 | 3.425 | 358.615 | 169.134 | 141.134 | 24.178 | 1 | yes |
| persia | passive | 10.379 | 0 | 0 | 33.625 | 44.004 | 1.583 | 69.658 | 477.721 | 323.06 | 300.06 | 42.403 | 3 | yes |
| aleppo | steer | 168.127 | 0 | 0 | 107.451 | 292.578 | 1.869 | 546.828 | 646.072 | 259.006 | 214.006 | 37.772 | 1 | yes |
| alexandria | steer | 160.14 | 0 | 0 | 112.027 | 289.167 | 1.875 | 542.188 | 1054.341 | 342.753 | 253.753 | 41.239 | - | yes |
| astrakhan | passive | 0 | 0 | 0 | 10.462 | 10.462 | 1.098 | 11.487 | 269.778 | 140.858 | 98.858 | 26.661 | - | yes |
| crimea | steer | 52.312 | 3 | 1 | 75.423 | 147.735 | 1.648 | 243.467 | 566.095 | 262.028 | 222.028 | 30.756 | - | yes |
| constantinople | home | 377.115 | 0 | 0 | 28.553 | 410.668 | 1.895 | 778.215 | 802.109 | 384.115 | 377.115 | 112.908 | 1 | yes |
| tunis | passive | 0 | 0 | 0 | 3.648 | 3.648 | 2.11 | 7.697 | 601.671 | 60.064 | 60.064 | 14.976 | - | yes |
| ragusa | collect-away | 142.768 | 0 | 0 | 36.604 | 196.372 | 0.761 | 149.439 | 600.887 | 293.378 | 239.378 | 36.084 | 1 | yes |
| pest | passive | 1.278 | 0 | 0 | 0 | 1.278 | 1.452 | 1.855 | 484.932 | 244.332 | 142.332 | 24.495 | 2 | yes |
| wien | passive | 0 | 0 | 0 | 32.956 | 32.956 | 1.8 | 59.32 | 1049.737 | 467.783 | 306.783 | 51.62 | 7 | yes |
| champagne | passive | 0 | 0 | 0 | 3.648 | 3.648 | 2.11 | 7.697 | 1068.179 | 512.006 | 373.006 | 35.54 | 8 | yes |
| valencia | passive | 0 | 0 | 0 | 3.648 | 3.648 | 2.11 | 7.697 | 487.196 | 153.938 | 148.938 | 23.961 | 1 | yes |
| genua | passive | 18.24 | 63.5 | 20 | 0 | 81.74 | 2.11 | 172.471 | 903.949 | 829.355 | 611.355 | 104.96 | 10 | yes |
| venice | collect-away | 164.781 | 110.5 | 36 | 0 | 292.281 | 0.92 | 268.898 | 569.592 | 570.84 | 369.34 | 90.21 | 6 | yes |

## Data: Genoa (GEN) in the same save

| node | role | province | ship | ships# | prev | max_pow | max_demand | val | node.total | node.max | node.p_pow | node.highest_power | node.num_collectors | trade_company_region |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ethiopia | passive | 0 | 0 | 0 | 17.084 | 17.084 | 1.907 | 32.579 | 323.701 | 124.949 | 115.949 | 21.181 | 2 | yes |
| gulf_of_aden | passive | 0 | 0 | 0 | 17.084 | 17.084 | 1.907 | 32.579 | 918.916 | 445.046 | 226.546 | 30.66 | 5 | yes |
| aleppo | passive | 0 | 0 | 0 | 17.084 | 17.084 | 1.907 | 32.579 | 646.072 | 259.006 | 214.006 | 37.772 | 1 | yes |
| alexandria | steer | 85.423 | 0 | 0 | 47.573 | 154.996 | 1.835 | 284.417 | 1054.341 | 342.753 | 253.753 | 41.239 | - | yes |
| crimea | passive | 0 | 0 | 0 | 0 | 20 | 1.907 | 38.14 | 566.095 | 262.028 | 222.028 | 30.756 | - | yes |
| tunis | passive | 0 | 0 | 0 | 38.147 | 38.147 | 1.907 | 72.746 | 601.671 | 60.064 | 60.064 | 14.976 | - | yes |
| ragusa | passive | 0 | 0 | 0 | 47.573 | 47.573 | 1.907 | 90.721 | 600.887 | 293.378 | 239.378 | 36.084 | 1 | yes |
| wien | passive | 0 | 0 | 0 | 9.426 | 9.426 | 1.853 | 17.466 | 1049.737 | 467.783 | 306.783 | 51.62 | 7 | yes |
| saxony | steer | 0 | 0 | 0 | 0 | 22 | 1.853 | 40.766 | 1027.684 | 462.561 | 324.561 | 40.672 | 7 | yes |
| rheinland | steer | 0 | 0 | 0 | 0 | 22 | 1.845 | 40.59 | 1348.979 | 682.377 | 495.377 | 47.168 | 12 | yes |
| champagne | collect-away | 0 | 0 | 0 | 38.147 | 60.147 | 0.887 | 53.35 | 1068.179 | 512.006 | 373.006 | 35.54 | 8 | yes |
| valencia | passive | 0 | 0 | 0 | 38.147 | 38.147 | 1.759 | 67.1 | 487.196 | 153.938 | 148.938 | 23.961 | 1 | yes |
| genua | home | 190.737 | 47.5 | 15 | 0 | 265.237 | 1.241 | 329.159 | 903.949 | 829.355 | 611.355 | 104.96 | 10 | yes |
| venice | collect-away | 47.131 | 0 | 0 | 0 | 69.131 | 0.858 | 59.314 | 569.592 | 570.84 | 369.34 | 90.21 | 6 | yes |

TUR country data useful for the modifier question (from the save): technology adm/dip/mil 19/19/20, mercantilism 28.0, navy_tradition 60.442, idea groups (level) {TUR_ideas 7, trade_ideas 7, innovativeness_ideas 7, quantity_ideas 7, exploration_ideas 7, expansion_ideas 6}, government rank 3 (turkish_monarchy), 8 merchants, 100 light ships, religion sunni, institutions embraced 5 of 8, 3 subjects, active policies include the_banking_system, production_quota_act, beneficial_neglect.
