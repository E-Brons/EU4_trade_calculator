# R08 - How forwarded value is split across outgoing links (steering, add, trade_steering)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R08_steering_and_link_split_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R08_steering_and_link_split_draft.md`

```
# R08 results - How forwarded value is split across outgoing links (steering, add, trade_steering)
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

A node forwards `outgoing = gross - current` to its downstream nodes. Define the exact split across the outgoing links: the role of each steering merchant (`type` present, with `steer_power` = index of the link, absent = first link), of non-steering/passive power, the node field `steer_power = [w0, w1, ...]` (one weight per outgoing link in graph edge order), the per-country `add` (steering value bonus), the node's `incoming[].add`, `TRADE_ADDED_VALUE_MODIFER = 0.05` (+5% per steering merchant?), the country modifier `trade_steering`, and `value_added_outgoing` (equals `outgoing` in all nodes we checked; when does it differ?).

Give formulas for: (a) each link's value as a function of the node's gross value, retention, `steer_power` weights and bonuses; (b) how node-level `steer_power` weights are computed from country entries (which `val` or effective power is summed per link; how passive power is distributed; what happens when nobody steers); (c) `add` per steering country and per incoming link (how the +5% is computed and on what base, and who benefits); (d) whether `steer_power` weights sum to 1 (they do in the examples: 0.648+0.085+0.266 = 0.999).

## Example 1: node `alexandria` (real save): retention 0.0 (all value forwarded), outgoing 25.551, steer_power [0.648, 0.085, 0.266]

Graph outgoing links in order: ['constantinople', 'venice', 'genua']. Downstream `incoming` entries whose `from` is Alexandria (value, add): [['constantinople', [(18.759, 2.202)]], ['venice', [(2.425, 0.254)]], ['genua', [(7.455, 0.659)]]].

| tag | role | val | country steer_power (link index) | add | merchant |
|---|---|---|---|---|---|
| TUR | steering | 542.188 | -(first link) | 0.092 | trader |
| GEN | steering | 284.417 | 2 | 0.072 | trader |
| SPA | non-collecting | 61.855 | 2 | 0 | - |
| PAP | steering | 46.597 | 1 | 0.078 | trader |
| BLG | steering | 38.54 | 1 | 0.039 | trader |
| LAN | non-collecting | 37.521 | 2 | 0 | - |
| SWI | non-collecting | 13.067 | -(first link) | 0 | - |
| HUN | steering | 9.506 | -(first link) | 0.025 | trader |
| HAB | non-collecting | 7.423 | -(first link) | 0 | - |
| SIE | steering | 7.361 | 2 | 0.025 | trader |
| CLI | non-collecting | 3.124 | 1 | 0 | - |
| WAL | steering | 2.742 | -(first link) | 0.016 | trader |

## Example 2: node `gulf_of_aden`: outgoing 16.981, retention 0.585, steer_power [0.217, 0.746, 0.036]

Graph outgoing links in order: ['zanzibar', 'alexandria', 'hormuz']. Downstream incoming (value, add): [['zanzibar', [(4.291, 0.607)]], ['alexandria', [(13.832, 1.165)]], ['hormuz', [(0.687, 0.076)]]].

| tag | role | val | country steer_power (link index) | add | merchant |
|---|---|---|---|---|---|
| AJU | collecting | 267.709 | -(first link) | 0 | trader |
| TUR | steering | 233.431 | 1 | 0.092 | trader |
| YEM | collecting | 164.117 | -(first link) | 0 | trader |
| HDR | collecting | 63.411 | -(first link) | 0 | - |
| GZI | steering | 38.713 | -(first link) | 0.028 | trader |
| GEN | non-collecting | 32.579 | -(first link) | 0 | - |
| MIR | steering | 30.021 | -(first link) | 0.09 | trader |
| MHR | collecting | 24.983 | -(first link) | 0 | - |
| ETH | collecting | 17.133 | 1 | 0 | trader |
| ANT | steering | 10.032 | -(first link) | 0.02 | trader |
| TRS | steering | 9.926 | 2 | 0.075 | trader |
| MLI | steering | 7.033 | -(first link) | 0.017 | trader |
| SPA | non-collecting | 5.688 | -(first link) | 0 | - |
| PTE | steering | 5.351 | -(first link) | 0.01 | trader |
| BRI | non-collecting | 3.601 | -(first link) | 0 | - |
| ISF | steering | 2.834 | 2 | 0.018 | trader |
| DAW | steering | 2.354 | 2 | 0.032 | trader |

(`steer_power` index 0 = first outgoing link, 1 = second, ...; countries without the key steer to the first link.)
