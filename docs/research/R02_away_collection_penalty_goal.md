# R02 - The penalty for collecting away from the capital node (TRADE_NON_CAPITAL_OFFICE = -0.5)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R02_away_collection_penalty_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R02_away_collection_penalty_draft.md`

```
# R02 results - The penalty for collecting away from the capital node (TRADE_NON_CAPITAL_OFFICE = -0.5)
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

`common/defines.lua` contains `TRADE_NON_CAPITAL_OFFICE = -0.50`. Establish **exactly how it works in 1.37.5**: when does it apply (collecting merchant away from the capital node? steering? merchants without collection? every non-capital node?), to which quantity (province power, ship power, merchant power, propagated `prev` power, or the final multiplier `max_demand`), and how it is offset by `reduced_trade_penalty_on_non_main_tradenode`, trade-company/subject rules, or anything else. Our older project notes wrongly claimed this penalty did not exist.

Data (below): in the save, countries that **collect away from their capital** (key `total` present, no `has_capital`) have a much smaller `max_demand` than the same country's median `max_demand` at nodes where it does not collect (ratio column; a ratio near 0.5 would match a -50%). `val = max_pow * max_demand` always, so the penalty is already inside `max_demand`. Ratios in the table are clearly not all 0.5 (some about 0.4, some 0.5, some above), so find what else is in the formula (e.g. penalty applied only to the non-propagated part, merchant power exempt, ship power exempt, `reduced_trade_penalty_on_non_main_tradenode` > 0).

Columns: `province`/`ship`/`prev` = raw power parts, `md` = this entry's `max_demand`, `median_md_elsewhere` = median `max_demand` of the same country at nodes where it is not collecting, `ratio` = md / median, `has_trader` = merchant present, `t_out` = power transferred out.

| tag | node | province | ship | prev | max_pow | md | median_md_elsewhere | ratio | has_trader | t_out |
|---|---|---|---|---|---|---|---|---|---|---|
| AYU | malacca | 17.256 | 0 | 0 | 19.256 | 0.679 | 1.357 | 0.5 | True | 0 |
| AYU | ganges_delta | 0 | 0 | 0 | 2 | 0.679 | 1.357 | 0.5 | True | 0 |
| BLG | genua | 8.58 | 0 | 0 | 25.58 | 0.794 | 1.587 | 0.5 | True | 0 |
| BRA | lubeck | 50.669 | 3.5 | 0 | 56.169 | 0.804 | 1.607 | 0.5 | True | 0 |
| BRI | champagne | 114.14 | 0 | 2.882 | 119.022 | 0.833 | 1.666 | 0.5 | True | 0 |
| BRI | english_channel | 14.411 | 16.5 | 0 | 32.911 | 0.833 | 1.666 | 0.5 | True | 0 |
| C02 | carribean_trade | 20.163 | 10 | 0 | 32.163 | 0.897 | 1.794 | 0.5 | True | 14.375 |
| C03 | panama | 17.362 | 10.5 | 0 | 44.862 | 0.772 | 1.543 | 0.5 | True | 17.266 |
| C04 | chesapeake_bay | 83.389 | 0 | 0 | 85.389 | 0.916 | 1.832 | 0.5 | True | 39.058 |
| C06 | brazil | 12.27 | 7 | 0 | 36.27 | 0.803 | 1.606 | 0.5 | True | 14.512 |
| C07 | ohio | 35.942 | 0 | 0 | 37.942 | 0.637 | 1.273 | 0.5 | True | 12.034 |
| CSH | beijing | 88.045 | 5 | 0 | 110.045 | 0.656 | 1.186 | 0.553 | True | 0 |
| CSH | yumen | 9.364 | 0 | 0 | 26.364 | 0.653 | 1.186 | 0.551 | True | 0 |
| DEC | comorin_cape | 241.199 | 44 | 29.5 | 331.699 | 0.72 | 1.875 | 0.384 | True | 0 |
| DEC | gujarat | 147.502 | 22.5 | 0 | 187.002 | 0.72 | 1.875 | 0.384 | True | 0 |
| DLH | lahore | 107.73 | 0 | 4.871 | 119.601 | 0.821 | 1.376 | 0.597 | True | 0 |
| DLH | gujarat | 24.358 | 0 | 0 | 31.358 | 0.688 | 1.376 | 0.5 | True | 0 |
| FRA | genua | 0 | 0 | 0 | 2 | 0.523 | 1.045 | 0.5 | True | 0 |
| GEN | champagne | 0 | 0 | 38.147 | 60.147 | 0.887 | 1.907 | 0.465 | True | 0 |
| GEN | venice | 47.131 | 0 | 0 | 69.131 | 0.858 | 1.907 | 0.45 | True | 0 |
| GZI | zanzibar | 88.789 | 18 | 0 | 108.789 | 0.639 | 1.301 | 0.491 | True | 0 |
| HAB | english_channel | 39.715 | 24.5 | 0 | 71.215 | 0.589 | 1.178 | 0.5 | True | 0 |
| HAI | english_channel | 15.084 | 0 | 0 | 22.084 | 0.729 | 1.457 | 0.5 | True | 0 |
| IRQ | aleppo | 45.879 | 0 | 0 | 47.879 | 0.686 | 1.372 | 0.5 | True | 0 |
| KHM | canton | 4.568 | 0 | 4.544 | 31.112 | 0.724 | 1.447 | 0.5 | True | 0 |
| KHM | malacca | 22.721 | 7.5 | 0 | 52.221 | 0.724 | 1.447 | 0.5 | True | 0 |
| KON | ivory_coast | 46.211 | 6 | 0 | 54.211 | 0.478 | 1.307 | 0.366 | True | 0 |
| LAN | venice | 37.762 | 0 | 0 | 39.762 | 0.638 | 1.413 | 0.452 | True | 0 |
| LIT | baltic_sea | 12.34 | 0 | 0 | 19.34 | 0.525 | 1.049 | 0.5 | True | 0 |
| MAL | ivory_coast | 36.954 | 0 | 0 | 53.954 | 0.736 | 1.606 | 0.458 | True | 0 |
| MNG | ganges_delta | 0 | 0 | 0 | 2 | 0.785 | 1.458 | 0.538 | True | 0 |
| MOR | ivory_coast | 97.018 | 0 | 0 | 99.018 | 0.389 | 1.323 | 0.294 | True | 0 |
| PAP | genua | 78.889 | 0 | 0 | 100.889 | 0.463 | 1.35 | 0.343 | True | 0 |
| RUS | baltic_sea | 107.971 | 2.5 | 0 | 127.471 | 0.631 | 1.418 | 0.445 | True | 0 |
| SON | ivory_coast | 2.095 | 0 | 0 | 19.095 | 0.545 | 1.485 | 0.367 | True | 0 |
| SPA | genua | 103.775 | 10 | 0 | 115.775 | 1.069 | 2.118 | 0.505 | True | 0 |
| SPA | english_channel | 53.948 | 0 | 0 | 55.948 | 0.7 | 2.118 | 0.331 | True | 0 |
| SUN | malacca | 3.231 | 0 | 0 | 20.231 | 0.703 | 1.522 | 0.462 | True | 0 |
| SWI | genua | 50.652 | 0 | 0 | 52.652 | 0.645 | 1.63 | 0.396 | True | 0 |
| TRI | champagne | 14.764 | 0 | 0 | 21.764 | 0.856 | 1.711 | 0.5 | True | 0 |
| TRS | persia | 57.09 | 0 | 0 | 64.09 | 0.709 | 1.418 | 0.5 | True | 0 |
| TUR | ragusa | 142.768 | 0 | 36.604 | 196.372 | 0.761 | 1.882 | 0.404 | True | 0 |
| TUR | venice | 164.781 | 110.5 | 0 | 292.281 | 0.92 | 1.882 | 0.489 | True | 0 |

Also answer: does a country collecting at its **capital node** (`has_capital`) ever get the penalty? (We see none.) Does a country whose capital is not in any trade node (colonial nation, etc.) get it everywhere?
