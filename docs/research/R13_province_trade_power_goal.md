# R13 - Per-province trade power and trade value (optional, lower priority)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R13_province_trade_power_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R13_province_trade_power_draft.md`

```
# R13 results - Per-province trade power and trade value (optional, lower priority)
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

Optional: allow us to recompute `province_power` and `local_value` from provinces. Define: (1) the exact formula for a province's trade power in its node: development (`province_trade_power_value` +0.2 per development in `static_modifiers`), centers of trade (+5/+10/+25 by level), estuary and harbour modifiers, `province_trade_power_modifier` (coastal +25%, buildings marketplace +50%, trade depot +100%, stock exchange +125%, trade company +100%, autonomy -50% scaled), `global_prov_trade_power_modifier` (mercantilism +2% per point), `local_autonomy`, occupation/blockade/siege, trade-company-region effects, caravan power (`CARAVAN_FACTOR = 3.0`, `CARAVAN_POWER_MAX = 50`, `CARAVAN_POWER_MIN = 2`); the save stores `trade_power=<float>` on each province (e.g. a province with `trade_power=41.670`), so state which of these are already included in that stored number. (2) The formula for a node's `local_value`: goods produced (development by production, `trade_goods_size`, modifiers) x goods price (`common/prices`), `trade_value_modifier`, trade company/merchant republic bonuses. (3) Are `province_power` of a country at a node the plain sum of `trade_power` of its provinces in the node's `members`? (We have not verified this.)

Known game-file facts (from `common/`): `province_trade_power_value` +0.2 per development; CoT staple_port/emporium +5 (level 1), entrepot/market_town +10, world_port/world_trade_center +25; estuaries +10 (Ganges/Nile/Irrawaddy +5); silk +2; trade company investments company_warehouse +2, company_depot +4; goods prices: grain/wine/wool/fish 2.5, cloth/salt/copper/iron/chinaware/spices/coffee/cotton/sugar/tobacco/glass 3, fur/naval_supplies/slaves/tea 2, ivory/cocoa/silk/dyes/gems 4, cloves 8, coal 10, paper 3.5, incense 2.5.
