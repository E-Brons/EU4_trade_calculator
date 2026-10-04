# R09 - Meaning of every trade-block field in an EU4 save

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R09_save_field_dictionary_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R09_save_field_dictionary_draft.md`

```
# R09 results - Meaning of every trade-block field in an EU4 save
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

For **every** field below give: exact meaning, unit, and (if derived) the formula that the game uses. Priority: `max_demand`, `prev`, `max_pow`, `already_sent`, `potential`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors`, `top_power`, `top_provinces`, `power_fraction`, `value_added_outgoing`, `t_in`/`t_out`/`t_from`/`t_to`, `add`, `trade_goods_size`. Look at pdx.tools / eu4save / rakaly source and schemas, EU4 modding wikis, Paradox forum threads on save-game structure, and any reverse-engineering write-ups. Our verified relations for several are in the header. Fields you cannot document: `UNKNOWN`.

Known per-save counts (REAL + S42 + S14, 320 nodes). Node-level fields (count, example value):

| field | count | example |
|---|---|---|
| definitions | 240 | african_great_lakes |
| retention | 240 | 0.316 |
| num_collectors_including_pirates | 240 | 3 |
| trade_goods_size | 240 | [0.0, 2.8, 0.0, 0.0, 0.0, 0.66, 0.0, 1.8, 0.0, 0.0, 0.0, 4.0 |
| most_recent_treasure_ship_passage | 240 | 1.1.1 |
| total | 239 | 184.883 |
| p_pow | 239 | 51.446 |
| max | 239 | 76.446 |
| highest_power | 239 | 17.371 |
| top_provinces | 239 | ['RWA', 'KRW'] |
| top_provinces_values | 239 | [45.278, 6.168] |
| top_power | 239 | ['RWA', 'KON', 'MIR', 'GZI', 'MLI', 'KRW', 'ANT', 'SPA', 'BR |
| top_power_values | 239 | [44.434, 35.542, 30.021, 23.101, 15.514, 13.839, 7.188, 5.68 |
| local_value | 238 | 2.891 |
| steer_power | 231 | [0.572, 0.427] |
| incoming | 219 | {'add': 0.064, 'value': 0.908, 'from': 1} |
| pull_power | 218 | 126.61 |
| outgoing | 217 | 1.977 |
| value_added_outgoing | 217 | 1.977 |
| current | 210 | 0.914 |
| num_collectors | 210 | 2 |
| collector_power | 210 | 58.273 |
| collector_power_including_pirates | 210 | 58.273 |
| retain_power | 210 | 58.273 |
| trade_company_region | 189 | True |

Country-in-node fields (count, example):

| field | count | example |
|---|---|---|
| max_demand | 100640 | 1.0 |
| max_pow | 3108 | 2.162 |
| val | 3084 | 3.601 |
| has_trader | 2238 | True |
| province_power | 1722 | 45.278 |
| prev | 1455 | 2.162 |
| power_fraction | 1303 | 0.762 |
| money | 1303 | 0.89 |
| total | 1303 | 0.696 |
| has_capital | 1255 | True |
| type | 979 | 1 |
| potential | 959 | -0.224 |
| already_sent | 656 | 25.194 |
| steer_power | 550 | 1 |
| add | 312 | 0.052 |
| t_out | 180 | 16.098 |
| t_to | 180 | {'POR': 16.098} |
| ship_power | 112 | 16.5 |
| light_ship | 112 | 5 |
| t_in | 103 | 52.326 |
| t_from | 103 | {'C08': 52.326} |
| modifier | 64 | {'key': 'merchant_recalled', 'duration': 1312, 'power': -10. |

Additional country-level fields in the same save that may matter: `trade_embargoes`, `trade_embargoed_by`, `transfer_trade_power_from`, `transfer_trade_power_to`, `merchants={envoy={...}}` (action/type per merchant), `traded`, `traded_bonus`, `trade_mission`, `num_ships_protecting_trade`, `mercantilism`, province field `trade_power`, node `trade_company_region`. Document these as well if sources exist.
