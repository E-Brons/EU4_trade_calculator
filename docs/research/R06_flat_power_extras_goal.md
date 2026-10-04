# R06 - Flat power additions: capital, merchants, placed_merchant_power, modifiers

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R06_flat_power_extras_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R06_flat_power_extras_draft.md`

```
# R06 results - Flat power additions: capital, merchants, placed_merchant_power, modifiers
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

Define every flat (non-province, non-ship, non-propagated) addition to a country's `max_pow` at a node, and when each applies. We compute `extras = max_pow - province_power - ship_power - prev` per entry. Observed (all 80 saves, counts of the most common values by role):

| role (+merchant = has_trader) | entries | most common extras value: count |
|---|---|---|
| collect-away+merchant | 49 | 2.0: 21; 17.0: 13; 7.0: 10; 22.0: 5 |
| home | 5801 | 5.0: 5799; 7.0: 1; -5.0: 1 |
| home+merchant | 36480 | 5.0: 36366; 7.0: 68; 22.0: 17; 12.0: 12; -3.0: 11; 27.0: 5; 2.0: 1 |
| passive | 15744 | 0.0: 15741; 20.0: 2; -10.0: 1 |
| passive+merchant | 4939 | 0.0: 4831; 20.0: 107; 2.0: 1 |
| steer+merchant | 20188 | 0.0: 19768; 2.0: 246; 17.0: 88; 22.0: 38; 7.0: 38; -8.0: 6; 42.0: 2 |

Defines: `TRADE_CAPITAL_POWER = 5.0`, `MERCHANT_MAX_POWER_BONUS = 2.0`, `TRADE_POWER_HOME_BONUS = 0.1`, `TRADE_POWER_HOME_BONUS_MAX = 1`. Country modifier `placed_merchant_power` (+15 from trade ideas "overseas merchants", +5/+10 from estate privileges; the game's `common/` data), `placed_merchant_power_modifier`, and a node-level `modifier = { key duration power power_modifier }` block on country entries (seen: `merchant_recalled power=-10`, `pirate_hunting power=-10`).

Our hypotheses (confirm or refute with sources): capital node always gets +5 (with or without merchant); a merchant **collecting away** adds +2 (`MERCHANT_MAX_POWER_BONUS`) plus `placed_merchant_power`; a **steering** merchant usually adds 0 (98% of the time) - but sometimes 2/7/12/17/22/27, which equals 2 + placed_merchant_power in {0,5,10,15,...} combinations (`17 = 2+15`, `7 = 2+5`, `12 = 2+10`, `22 = 2+15+5`, `27 = 2+15+10`) and `-10` equals the `merchant_recalled` modifier. Why do most steering merchants add 0 while some add 2 (+placed)? Is the +2 only for merchants that are *collecting*? Does `placed_merchant_power` apply to steering? Is `power_modifier` (the node-modifier field) multiplicative? What does `TRADE_POWER_HOME_BONUS` (+10%, max 1) apply to, and is it included in `max_pow` or in `max_demand`?

## Entries with unusual extras in the real save (not 0, 2 or 5), with their node modifier block

| node | country | role | extras | modifier block |
|---|---|---|---|---|
| african_great_lakes | RWA | home+merchant | -3 | key:merchant_recalled,duration:1312,power:-10,power_modifier:0 |
| african_great_lakes | KRW | home+merchant | 7 | - |
| african_great_lakes | MIR | steer+merchant | 17 | - |
| kongo | BEN | steer+merchant | 17 | - |
| kongo | KON | home+merchant | 7 | - |
| kongo | MAL | steer+merchant | 17 | - |
| kongo | SON | steer+merchant | 17 | - |
| zambezi | GZI | home+merchant | 7 | - |
| zambezi | TBK | home+merchant | 7 | - |
| patagonia | MPC | home+merchant | 7 | - |
| patagonia | C01 | steer+merchant | 22 | - |
| patagonia | C03 | steer+merchant | 17 | - |
| patagonia | C06 | steer+merchant | 7 | key:merchant_recalled,duration:2601,power:-10,power_modifier:0 |
| amazonas_node | C01 | steer+merchant | 22 | - |
| amazonas_node | C03 | steer+merchant | 17 | - |
| amazonas_node | C06 | steer+merchant | 17 | - |
| rio_grande | NAH | home+merchant | 7 | - |
| rio_grande | ZNI | home+merchant | 7 | - |
| rio_grande | ACO | home+merchant | 7 | - |
| rio_grande | C03 | steer+merchant | 17 | - |
| rio_grande | C11 | home+merchant | 12 | - |
| rio_grande | C16 | steer+merchant | 7 | - |
| james_bay | BLA | home+merchant | 7 | - |
| james_bay | ARP | home+merchant | 7 | - |
| james_bay | NEH | home+merchant | 7 | - |
| james_bay | C05 | steer+merchant | 17 | - |
| james_bay | C17 | home+merchant | 12 | - |
| california | PIM | home+merchant | 7 | - |
| california | SHO | home+merchant | 7 | - |
| california | CNK | home+merchant | -3 | key:merchant_recalled,duration:1996,power:-10,power_modifier:0 |
| california | HDA | home+merchant | -3 | key:merchant_recalled,duration:534,power:-10,power_modifier:0 |
| california | YAQ | home+merchant | 7 | - |
| california | C03 | steer+merchant | 17 | - |
| california | C15 | home+merchant | -3 | key:merchant_recalled,duration:1146,power:-10,power_modifier:0 |
| california | C16 | home+merchant | 12 | - |
| california | C19 | home+merchant | 7 | - |
| girin | MHX | home+merchant | 12 | key:merchant_recalled,duration:320,power:-10,power_modifier:0 |
| girin | CHC | steer+merchant | 17 | - |
| girin | WUU | steer+merchant | 17 | - |
| girin | HOD | home+merchant | 7 | - |
