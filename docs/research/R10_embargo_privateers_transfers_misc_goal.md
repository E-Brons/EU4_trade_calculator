# R10 - Embargo, privateers/pirates and why node total can differ from the sum of country val

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R10_embargo_privateers_transfers_misc_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R10_embargo_privateers_transfers_misc_draft.md`

```
# R10 results - Embargo, privateers/pirates and why node total can differ from the sum of country val
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

(1) **Privateers/pirates.** Define how privateer power enters a node (`PIRATES_TRADE_POWER_FACTOR = 1.5`, `PIRATES_MONOPOLY_BONUS = 1`, `privateer_efficiency`, `PRIVATEER_INCOME_COLLECTION_EFF = 0.5`), how `collector_power_including_pirates` / `num_collectors_including_pirates` differ from `collector_power` / `num_collectors`, and why in some nodes `total` is larger than the sum of the listed countries' `val` (table below; the `PIR` entry often has no `val`). Does pirate power appear in `retain_power`/`pull_power`? Where is it recorded?
(2) **Embargo.** How an embargo (`trade_embargoes`, `trade_embargoed_by` on a country; `EMBARGO_BASE_EFFICIENCY = 0.5`, `EMBARGO_MERCANTILISM_EFFICIENCY = 50`, `embargo_efficiency`) changes an embargoed country's trade power in nodes and/or its income. TUR in this save is embargoed by ['HUN', 'HAB', 'LUN', 'RUS', 'BNG', 'DEC'], and embargoes None. Is the effect already inside `max_demand` or `val`, or only in `money`?
(3) Which other node-level effects (monopoly bonus, trade company region, blockade, treasure fleets) alter value or power and where do they appear in the saved fields?

## Nodes where `total` differs from the sum of country `val` by more than 2% (all saves; first 25 by absolute gap)

| save | node | node.total | sum(val of entries) | gap | PIR entry has val |
|---|---|---|---|---|---|
| S68 | sevilla | 329.161 | 291.222 | 37.939 | no |
| S70 | sevilla | 329.068 | 291.129 | 37.939 | no |
| S36 | persia | 213.238 | 184.379 | 28.859 | no |
| S53 | constantinople | 182.621 | 156.303 | 26.318 | no |
| S68 | alexandria | 290.259 | 264.536 | 25.723 | no |
| S70 | alexandria | 290.259 | 264.536 | 25.723 | no |
| S36 | hormuz | 108.398 | 83.288 | 25.11 | no |
| S56 | bordeaux | 143.364 | 124.046 | 19.318 | no |
| S57 | bordeaux | 143.364 | 124.046 | 19.318 | no |
| S71 | cuiaba | 145.015 | 130.614 | 14.401 | no |
| S68 | cuiaba | 164.186 | 149.917 | 14.269 | no |
| S70 | cuiaba | 181.726 | 167.457 | 14.269 | no |
| S74 | cuiaba | 144.644 | 130.375 | 14.269 | no |
| S72 | cuiaba | 141.99 | 128.083 | 13.907 | no |
| S57 | kiev | 143.696 | 129.879 | 13.817 | no |
| S41 | kiev | 142.837 | 129.02 | 13.817 | no |
| S56 | kiev | 142.837 | 129.02 | 13.817 | no |
| S68 | valencia | 171.131 | 157.877 | 13.254 | no |
| S70 | valencia | 171.131 | 157.877 | 13.254 | no |
| S73 | cuiaba | 142.246 | 129.298 | 12.948 | no |
| S53 | aleppo | 169.707 | 156.942 | 12.765 | no |
| S56 | champagne | 367.246 | 355.13 | 12.116 | no |
| S57 | champagne | 366.61 | 354.494 | 12.116 | no |
| S36 | basra | 156.905 | 145.219 | 11.686 | no |
| S68 | tunis | 311.029 | 301.322 | 9.707 | no |

## Nodes where num_collectors != num_collectors_including_pirates (first 15 of 5703)

| save | node | num_collectors | incl_pirates | collector_power | collector_power_incl_pirates | retain_power | total | sum(val) |
|---|---|---|---|---|---|---|---|---|
| REAL | african_great_lakes | 2 | 3 | 58.273 | 58.273 | 58.273 | 184.883 | 184.883 |
| REAL | kongo | 1 | 2 | 138.941 | 138.941 | 138.941 | 267.868 | 267.868 |
| REAL | zambezi | 2 | 3 | 167.011 | 167.011 | 167.011 | 210.077 | 210.077 |
| REAL | patagonia | 1 | 2 | 12.86 | 12.86 | 12.86 | 232.936 | 232.936 |
| REAL | amazonas_node | 1 | 2 | 50.306 | 50.306 | 50.306 | 441.019 | 441.019 |
| REAL | rio_grande | 4 | 5 | 63.858 | 63.858 | 63.858 | 431.715 | 431.715 |
| REAL | james_bay | 4 | 5 | 53.985 | 53.985 | 53.985 | 252.321 | 252.321 |
| REAL | california | 9 | 10 | 129.462 | 129.462 | 129.462 | 490.772 | 490.772 |
| REAL | girin | 3 | 4 | 64.61 | 64.61 | 64.61 | 438.463 | 437.256 |
| REAL | mississippi_river | 2 | 3 | 62.771 | 62.771 | 62.771 | 455.215 | 455.215 |
| REAL | ohio | 3 | 4 | 33.514 | 33.514 | 33.514 | 473.82 | 473.82 |
| REAL | mexico | 2 | 3 | 336.162 | 336.162 | 336.162 | 836.07 | 836.07 |
| REAL | gulf_of_siam | 2 | 3 | 304.105 | 304.105 | 304.105 | 695.652 | 695.652 |
| REAL | canton | 3 | 4 | 152.051 | 152.051 | 152.051 | 683.437 | 683.437 |
| REAL | philippines | 5 | 6 | 264.246 | 264.246 | 264.246 | 424.033 | 424.033 |
