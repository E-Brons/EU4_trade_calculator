# R04 - Transferred trade power (t_in/t_out/t_from/t_to/potential) and subject/overlord trade rules

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R04_transferred_trade_power_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R04_transferred_trade_power_draft.md`

```
# R04 results - Transferred trade power (t_in/t_out/t_from/t_to/potential) and subject/overlord trade rules
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

Each country entry may carry `t_out` (power it gives away), `t_to` (map: receiver tag -> amount), `t_in` (power it receives), `t_from` (map: giver tag -> amount) and `potential`. Verified: a country's power for the retain/pull sums is `val - t_out + t_in`; `val` itself is `max_pow * max_demand` and does **not** include `t_in` or exclude `t_out`. Colonial nations (C00..C19) transfer almost all their power to their overlord (e.g. C03 -> SPA). SND (a subject/vassal of TUR) transfers a small part to TUR.

Explain the full mechanics in 1.37.5: (a) which diplomatic/subject mechanisms create transfers (`transfer_trade_power` in `common/subject_types`, the "transfer trade power" diplomatic action `transfer_trade_power_from/to` in the country block, peace-deal `PO_TRADE_POWER_AMOUNT`, colonial nations, trade companies, trade leagues, merchant republic vassals); (b) the **exact amount formula** (fraction of the giver's `val`? of `max_pow`? `t_out` as seen: C03 at Mexico transfers 334.426 of val 668.952, i.e. about 0.4999; C00 39.679 of 79.459 about 0.4994; C02 23.716 of 47.533; C04 2.44 of 4.981; C11 1.535 of 3.171; SND at hormuz 0.977 of 2.055 about 0.4754) - what produces ~0.5 and the small deviations?; (c) what `potential` means (small signed numbers; positive for givers, negative for receivers, e.g. C03 +0.399, SPA -0.475); (d) whether the receiver's `max_pow`/`val` are unaffected as seen, and how the receiver's income share is computed (the receiver's `power_fraction`/`money`); (e) whether the giver still collects with its remaining power (C03 collects at Mexico, `money` 20.548, `power_fraction` 0.995).

## Data: node `mexico` (real save): retain_power 336.162 (= (668.952-334.426) + (3.171-1.535)), pull_power 499.908, total 836.07

| tag | role | val | max_pow | t_out | t_to | t_in | t_from | potential |
|---|---|---|---|---|---|---|---|---|
| C03 | collecting | 668.952 | 440.68 | 334.426 | SPA:334.426 | 0 | - | 0.399 |
| C00 | steering | 79.459 | 47.495 | 39.679 | SPA:39.679 | 0 | - | 0.047 |
| C02 | steering | 47.533 | 26.496 | 23.716 | SPA:23.716 | 0 | - | 0.028 |
| HOL | non-collecting | 8.753 | 7.331 | 0 | - | 0 | - | 0 |
| C04 | non-collecting | 4.981 | 2.719 | 2.44 | POR:2.44 | 0 | - | 0.002 |
| SPA | steering | 4.274 | 2 | 0 | - | 397.821 | C00:39.679,C02:23.716,C03:334.426 | -0.475 |
| MCA | non-collecting | 3.738 | 2.891 | 0 | - | 0 | - | 0 |
| POR | non-collecting | 3.659 | 2.04 | 0 | - | 3.975 | C04:2.44,C11:1.535 | -0.004 |
| C11 | collecting | 3.171 | 7 | 1.535 | POR:1.535 | 0 | - | 0.001 |
| TOG | non-collecting | 3.085 | 2.116 | 0 | - | 0 | - | 0 |
| WAI | non-collecting | 3.023 | 2.595 | 0 | - | 0 | - | 0 |
| FRA | non-collecting | 2.768 | 2.649 | 0 | - | 0 | - | 0 |
| OAH | non-collecting | 2.674 | 2.282 | 0 | - | 0 | - | 0 |

pull_power 499.908 is reproduced exactly as the sum over non-collecting countries of (val - t_out + t_in): C00 39.78 + C02 23.817 + HOL 8.753 + C04 2.541 + SPA (4.274 + 397.821) + MCA 3.738 + POR (3.659 + 3.975) + TOG 3.085 + WAI 3.023 + FRA 2.768 + OAH 2.674.

Another example, node `hormuz`: TUR val 341.467 with t_in 0.977 from SND; SND val 2.055, t_out 0.977, potential +0.002 (TUR -0.002).

Also answer: which transferred amounts are taken from which part of the giver's power (province, ship, prev)? Do transfers propagate to other nodes? Why are only some countries' transfers 0.5 exactly (rounding or a different rule)?
