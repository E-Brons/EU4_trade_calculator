# R07 - Income formula, merchant-present bonus and how to compute trade efficiency

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R07_income_and_trade_efficiency_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R07_income_and_trade_efficiency_draft.md`

```
# R07 results - Income formula, merchant-present bonus and how to compute trade efficiency
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

Per collecting country at a node the save gives `money` (monthly ducats) and `total` (its share of the node's retained ducats). We find `money = total * (1 + X)` with `X` constant across a country's nodes except +0.10 where a merchant is present away from home. Define **exactly**: (1) the income formula (what is multiplied by what: node value share, trade efficiency, `TRADE_MERCHANT_PRESENT = 0.1`, tariffs, privateer/embargo effects, trade company, `global_trade_goods...`?); (2) when `TRADE_MERCHANT_PRESENT` applies (collecting merchant at home? away? any merchant?) - at the Ottoman capital with **no** merchant X = 0.75, at two away nodes with a collecting merchant X = 0.85; across all AI countries at their home node, countries with `has_trader=yes` do NOT show +0.10 versus those without (median X equal), which contradicts the idea that a merchant at home earns +0.10; (3) **the complete list of `trade_efficiency` sources and how to compute the country's value from data present in a save** (technology level, ideas by level, policies, government reforms, estate privileges, religion, buildings, event/static modifiers - the game's `common/` files define them; the save stores the *selections* but not the total). The expected value for the Ottomans in this save is **trade_efficiency = 0.75** (`X` at the merchant-less home node); please compute it from the data below as a check, listing each contribution with its source (`trade_efficiency` modifier keys appear in ideas, policies, technologies (+0.02 per diplomatic level?), religions, privileges, event modifiers).

Also explain why many 1444 countries show X = 0.07 exactly (and others 0.0, 0.05, 0.12, 0.17, 0.22, 0.27, 0.37): which base value and which early modifiers.

## Data: TUR collecting nodes, real save (X = money/total - 1)

| node | money | total | X | has_trader | has_capital | situation |
|---|---|---|---|---|---|---|
| constantinople | 123.313 | 70.465 | 0.75 | False | True | home, no merchant |
| ragusa | 4.371 | 2.363 | 0.85 | True | False | collect (merchant) away |
| venice | 20.729 | 11.205 | 0.85 | True | False | collect (merchant) away |

Across countries in the same save, each country's away-collecting X minus its home X is exactly +0.10 when the home node has no merchant (16 of 16 pairs) and 0.00 when the home node has a merchant (33 of 33 pairs).

## TUR country data from the save (selections only; modifier totals are not stored)

- technology: {'adm_tech': 19, 'dip_tech': 19, 'mil_tech': 20}
- mercantilism: 28.0; navy_tradition: 60.442; religion: sunni; government: turkish_monarchy, rank 3
- idea groups (level): {'TUR_ideas': 7, 'trade_ideas': 7, 'innovativeness_ideas': 7, 'quantity_ideas': 7, 'exploration_ideas': 7, 'expansion_ideas': 6}
- policies: [{'policy': 'the_banking_system', 'date': '1536.6.1'}, {'policy': 'production_quota_act', 'date': '1558.7.11'}, {'policy': 'beneficial_neglect', 'date': '1611.8.1'}, {'policy': 'the_garrison_act', 'date': '1558.7.11'}, {'policy': 'hired_adventurers_act', 'date': '1611.8.1'}]
- government: {'government': 'monarchy', 'reform_stack': {'reforms': ['monarchy_mechanic', 'ottoman_government', 'quash_noble_power_reform', 'ottoman_provincial_government_system_reform', 'maintain_clergy_balance_of_power_reform', 'organized_military_staff_reform', 'parliamentary_reform', 'dyanstic_administration_reform', 'thalassocracy_reform', 'six_livres_reform'], 'history': ['ottoman_government', 'quash_noble_power_reform', 'ottoman_provincial_government_system_reform', 'maintain_clergy_balance_of_power_reform', 'organized_military_staff_reform', 'parliamentary_reform', 'dyanstic_administration_reform', 'thalassocracy_reform', 'six_livres_reform']}}
- estate privileges: estate_church: ['estate_church_clerical_ministers', '1619.4.17'],['estate_church_clerical_oversight', '1444.11.11'],['estate_church_one_faith_one_culture', '1634.4.17']; estate_burghers: ['estate_burghers_commercial_board_of_advice', '1483.9.17'],['estate_burghers_free_enterprise', '1444.11.11'],['estate_burghers_land_trade_rights', '1508.9.17']
- institutions: [1, 1, 1, 1, 1, 0, 0, 0]
- active modifiers (keys): the_devshirme_system, tur_janissary, house_of_worship, thalassocracy, dhimmi_building_restrictions, india_trade_co, separation_of_powers, recent_liaising_advisor_timer, janissaries_denied_reward, khalifah, sect_practices, muslim_enforced_religion, recently_annexed_other_religion_timer, government_investment, poor_merchants, discontent_sowed
