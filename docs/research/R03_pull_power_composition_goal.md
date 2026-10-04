# R03 - Which countries' power counts in pull_power (and why some non-collectors are excluded)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R03_pull_power_composition_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R03_pull_power_composition_draft.md`

```
# R03 results - Which countries' power counts in pull_power (and why some non-collectors are excluded)
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

`retention = retain_power / (retain_power + pull_power)` is exact. We know `retain_power = sum over collecting countries of (val - t_out + t_in)` exactly. We do **not** know which non-collecting countries contribute to `pull_power`. The obvious guess `pull_power = sum over non-collecting countries of (val - t_out + t_in)` is wrong for most nodes: in 5588 nodes that have `pull_power`, only 2348 match; in 2729 more we can identify, by unique subset-sum, exactly which non-steering countries must be **excluded** (their effective power is in `total` but not in `pull_power`); 99 ambiguous, 412 where no subset of non-steering countries reproduces it.

Find the exact rule: which countries (by merchant presence, steering, province power vs propagated-only power, propagation threshold `TRADE_PROPAGATE_THRESHOLD = 2`, embargo, war, subject status, trade league, diplomatic relation to the node owner, ...) are counted in `pull_power`, `retain_power`, or neither. Note exclusion varies **by node within the same country** (e.g. TUR is excluded at 4 nodes, included at 17 in the real save), so it is not a pure country attribute. In the nodes we could solve, steering countries (`type` present) were always included (the 412 unsolved nodes might involve exclusions among them). Countries with neither collecting nor steering and no merchant (typically AI countries with provinces in the node) are the interesting ones. Also determine how the value that those countries "pull" is forwarded (by which weights) when nobody steers.

## Worked example: node `xian` (real save): retain_power 191.452, pull_power 56.459, total 261.611

| tag | role | val | province_power | prev | merchant |
|---|---|---|---|---|---|
| CHC | collecting | 112.619 | 39.373 | 0 | trader |
| CSH | collecting | 78.833 | 21.408 | 17.609 | trader |
| QIC | steering | 28.841 | 18.08 | 6.875 | trader |
| RUS | non-collecting | 20.135 | 1.944 | 12.256 | - |
| MNG | non-collecting | 7.737 | 5.831 | 0 | - |
| BNG | non-collecting | 5.963 | 4.648 | 0 | - |
| SHY | non-collecting | 4.192 | 0 | 2.665 | - |
| TRS | non-collecting | 3.291 | 0 | 2.321 | - |

Non-collecting effective sum = 28.841+20.135+7.737+5.963+4.192+3.291 = 70.159 but pull_power is 56.459; the difference 13.700 = MNG 7.737 + BNG 5.963 exactly (both province-only, no merchant). Another: node `hormuz`: pull_power 363.19, non-collecting effective sum 411.646 - 48.456 = YEM 47.378 + SND (2.055 - 0.977 transferred out) 1.078 excluded; TRS (province 3.947, no merchant) is included.

## Labelled sample (random, from all 80 saves): non-steering non-collecting countries, EXCLUDED vs included from pull_power

| save | node | tag | label | val | province | ship | prev | t_out | t_in | merchant | already_sent | max_demand |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S11 | timbuktu | SOS | included | 2.963 | 0 | 0 | 2.877 | 0 | 0 | - | - | 1.03 |
| S18 | valencia | LUC | included | 2.855 | 0 | 0 | 2.73 | 0 | 0 | - | - | 1.046 |
| S46 | baltic_sea | LIT | EXCLUDED | 7.2 | 6 | 0 | 0 | 0 | 0 | trader | - | 1.2 |
| S11 | lahore | SHY | EXCLUDED | 4.09 | 0 | 0 | 4.054 | 0 | 0 | - | - | 1.009 |
| S19 | comorin_cape | HDR | included | 2.59 | 0 | 0 | 2.28 | 0 | 0 | - | - | 1.136 |
| S33 | comorin_cape | ADE | included | 4.517 | 0 | 0 | 4.34 | 0 | 0 | - | - | 1.041 |
| S49 | beijing | CHG | included | 3.648 | 0 | 0 | 3.468 | 0 | 0 | - | - | 1.052 |
| S73 | ganges_delta | NAG | included | 7.069 | 4.642 | 0 | 0 | 0 | 0 | trader | - | 1.523 |
| S23 | kiev | GOL | EXCLUDED | 1.937 | 1.92 | 0 | 0 | 0 | 0 | trader | - | 1.009 |
| S04 | tunis | MLO | included | 5.86 | 0 | 0 | 5.808 | 0 | 0 | - | - | 1.009 |
| S53 | alexandria | FRA | included | 8.809 | 0 | 0 | 6.866 | 0 | 0 | - | - | 1.283 |
| S05 | timbuktu | BEN | included | 5.839 | 0 | 0 | 5.692 | 0 | 0 | - | - | 1.026 |
| S12 | astrakhan | GEN | included | 7.615 | 0 | 0 | 8.145 | 0 | 0 | - | - | 0.935 |
| S49 | astrakhan | TUR | included | 13.626 | 0 | 0 | 10.823 | 0 | 0 | - | - | 1.259 |
| S75 | alexandria | ANZ | EXCLUDED | 0.865 | 0.78 | 0 | 0 | 0 | 0 | trader | - | 1.109 |
| S59 | yumen | QNG | EXCLUDED | 59.746 | 41.81 | 0 | 0 | 0 | 0 | trader | already_sent | 1.429 |
| S55 | timbuktu | AIR | EXCLUDED | 1.731 | 1.432 | 0 | 0 | 0 | 0 | trader | - | 1.209 |
| S45 | north_sea | BRE | included | 6.599 | 0 | 0 | 6.37 | 0 | 0 | - | - | 1.036 |
| S70 | ivory_coast | POR | EXCLUDED | 61.946 | 21.495 | 0 | 18.548 | 0 | 0 | trader | already_sent | 1.547 |
| S51 | lubeck | BRA | EXCLUDED | 1.311 | 1.3 | 0 | 0 | 0 | 0 | - | - | 1.009 |
| S09 | kiev | GOL | EXCLUDED | 1.937 | 1.92 | 0 | 0 | 0 | 0 | trader | - | 1.009 |
| S34 | valencia | LAN | included | 8.672 | 0 | 0 | 8.291 | 0 | 0 | - | - | 1.046 |
| S53 | tunis | TUS | included | 10.806 | 0 | 0 | 10.282 | 0 | 0 | - | - | 1.051 |
| S14 | lahore | VIJ | EXCLUDED | 2.769 | 0 | 0 | 2.673 | 0 | 0 | - | - | 1.036 |
| S60 | siberia | ZUN | EXCLUDED | 7.061 | 0.733 | 0 | 5.108 | 0 | 0 | trader | - | 1.209 |
| S67 | baltic_sea | PRU | EXCLUDED | 104.571 | 79.344 | 0 | 5.467 | 0 | 0 | trader | already_sent | 1.233 |
| S10 | ragusa | URB | included | 2.188 | 0 | 0 | 2.146 | 0 | 0 | - | - | 1.02 |
| S49 | ragusa | FER | included | 4.393 | 0 | 0 | 4.282 | 0 | 0 | - | - | 1.026 |
| S36 | ivory_coast | KON | EXCLUDED | 19.51 | 18.599 | 0 | 0 | 0 | 0 | - | already_sent | 1.049 |
| S09 | ragusa | BYZ | EXCLUDED | 4.213 | 4.521 | 0 | 0 | 0 | 0 | - | - | 0.932 |
| S58 | astrakhan | KZH | EXCLUDED | 8.704 | 7.2 | 0 | 0 | 0 | 0 | - | - | 1.209 |
| S13 | tunis | PRO | EXCLUDED | 6.61 | 0 | 0 | 6.532 | 0 | 0 | - | - | 1.012 |
| S07 | lubeck | BRA | EXCLUDED | 1.21 | 1.2 | 0 | 0 | 0 | 0 | - | - | 1.009 |
| S11 | tunis | MOR | EXCLUDED | 4.847 | 0 | 0 | 4.688 | 0 | 0 | trader | - | 1.034 |
| S24 | ragusa | GEN | included | 11.16 | 0 | 0 | 11.936 | 0 | 0 | - | - | 0.935 |
| S48 | beijing | OIR | included | 3.461 | 0 | 0 | 3.838 | 0 | 0 | - | - | 0.902 |
| S06 | gulf_of_aden | ETH | EXCLUDED | 0.694 | 0.693 | 0 | 0 | 0 | 0 | - | - | 1.002 |
| S10 | comorin_cape | AJU | included | 2.287 | 0 | 0 | 2.208 | 0 | 0 | - | - | 1.036 |
| S76 | saxony | FRA | included | 3.811 | 0 | 0 | 2.519 | 0 | 0 | - | - | 1.513 |
| S14 | rheinland | SWE | EXCLUDED | 2.162 | 0 | 0 | 2.114 | 0 | 0 | - | - | 1.023 |
| S32 | rheinland | HAB | EXCLUDED | 4.941 | 4.715 | 0 | 0 | 0 | 0 | - | - | 1.048 |
| S04 | gulf_of_aden | SFA | included | 5.383 | 0 | 0 | 5.278 | 0 | 0 | - | - | 1.02 |
| S71 | lubeck | NOR | EXCLUDED | 22.905 | 15.04 | 0 | 0 | 0 | 0 | trader | already_sent | 1.523 |
| S47 | gujarat | MLI | included | 2.411 | 0 | 0 | 2.364 | 0 | 0 | - | - | 1.02 |

Note the attribute combinations of excluded entries are not separable by their own listed fields (province power yes/no, prev yes/no, merchant yes/no, already_sent yes/no all occur on both sides), so the rule must involve something else: other nodes, country-level state, ordering, or a threshold. If a source describes how the game decides who "pulls", quote it.
