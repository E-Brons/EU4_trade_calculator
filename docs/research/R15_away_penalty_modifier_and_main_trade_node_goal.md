# R15 - The away-penalty modifier and the main trade node (side questions of R02)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R15_away_penalty_modifier_and_main_trade_node_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 86 saved games (78 game-start/hands-off snapshots and 8 saves of one played Ottoman campaign, 1665-1696) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Verified facts (ground truth from the save corpus; do not contradict them, build on them)

These come from the closed topic R02 (penalty for collecting away from the capital node), verified over 84 distinct saves.

- F1. A merchant that **collects** at a node other than the country's home node (key `total` present, no key `has_capital`) has `max_demand` equal to exactly **0.5 x** the value the same country has at its other, unpenalised nodes of the same class: 188 of 189 testable entries (the one exception is a further, unrelated reduction); other factors (0.3, 0.4, 0.55, 0.6, 0.7) match none. The halving is multiplicative on the whole `max_demand`; `val = max_pow * max_demand` (so the power of every component at that node is halved in effect).
- F2. Steering merchants (key `type`), merchants without action (`has_trader` but neither `type` nor `total`) and collectors at their home node are not halved (0 of 21,969 steering entries, 1 of 5,033 action-less merchants - which is a collector lacking the key `total` - and 0 of 42,853 home collectors are at half).
- F3. In every testable away row the factor is exactly 0.5, i.e. the modifier `reduced_trade_penalty_on_non_main_tradenode` (if a country had it) is **0 in all of them**: 188 entries = 47 distinct (country, node) pairs of 38 countries, all from one campaign (saves dated 1665.4.22, 1682.4.18, 1691.1.9, 1691.11.1, 1693.4.15, 1696.3.25); the 78 game-start snapshots contain no away collector. The modifier is **not stored** in the save: the string `reduced_trade_penalty` occurs 0 times in the full text of the saves checked (dated 1444.11.11, 1693.4.15 and 1696.3.25), which include a complete `countries` block with each country's `modifier` list.
- F4. The node entry that carries `has_capital` is always the node containing the province `countries.<TAG>.trade_port`: 42,978 of 42,978 countries that have the entry. The node containing `countries.<TAG>.capital` is the same node as the node of `trade_port` in **all** 115,920 country-saves that have a `trade_port`; the corpus therefore cannot show which of the two the game uses when they differ. Example: TUR, capital = trade_port = province 151, node `constantinople`, in all six campaign saves; in the last five saves `has_capital` is on the `constantinople` entry.
- F5. Colonial nations (tags C00-C17): the 534 country-saves that have trade data all have a `has_capital` entry; 53 of their away-collecting entries are all at exactly 0.5; the 5,766 colonial-tag country-saves without a `has_capital` entry are inactive tags (bare `max_demand` stubs only).
- F6. Examples of away rows (save S79, `max_demand` / value of the same country at other nodes of the same class): FRA genua 0.523 / 1.045; SPA genua 1.069 / 2.137; DEC comorin_cape 0.720 / 1.440; DLH lahore 0.821 / 1.642; GZI zanzibar 0.639 / 1.278; HAB english_channel 0.589 / 1.178. Within-country switch (TUR, gulf_of_aden): `max_demand` 1.932 (steering, 1691.1.9), 1.925 (steering, 1691.11.1), 1.145 (collecting away, 1693.4.15) while the steering control node crimea is 1.932, 1.925, 2.289.

## Questions

**Q1 - The modifier `reduced_trade_penalty_on_non_main_tradenode` in 1.37.5.** (a) Does this exact modifier key exist in 1.37.5 (give the file and line in `common/` or the modifier localisation / the wiki modifier list, and the version it refers to)? (b) Every source of it: ideas, policies, government reforms, religions, missions, decrees, great projects, estate privileges, events - with file + line, the value and the exact wording. (c) How it combines with the base penalty of -50% (`TRADE_NON_CAPITAL_OFFICE = -0.50`): added to the 0.5 factor before multiplying the country's trade power multiplier, `(1 + mods) * (0.5 + r)`, or as a separate term, `(1 + mods) * 0.5 + r`; is there a floor or cap (the wiki says bonuses "add onto the -50% base penalty"; quote the sentence with section and version). (d) Which countries or situations in the 1444-1821 period can have r > 0, so that we know which saved game should show it (F3 says r = 0 for the 38 countries tested).

**Q2 - The main trade node ("home node") when the capital and the main trade port differ.** (a) In the save, `countries.<TAG>.trade_port` (province id) and `countries.<TAG>.capital` exist and the node entry with `has_capital` follows `trade_port` (F4). Identify the game concept (main trade city / main trade port / capital trade node), the save field name in a parser project (pdx-tools, eu4save, rakaly: file path, struct or field, version), and quote it. (b) What does the game use as the node where the away penalty does NOT apply: the node of the capital province or the node of the main trade port (main trade city)? Sources for how the main trade city is chosen, that it moves "for free" with the capital, and what changes it (Wealth of Nations ability of the Trade idea group, the decision/button to move the main trade city, events) in 1.37.5, with quotes. (c) Does a colonial nation have a main trade city at all, and does it follow the same rule (F5)? (d) Is a merchant that collects at the home node always free of the penalty even when the country has moved its main trade port in the same month (timing: the monthly tick versus the save)?

## Required format of `R15_away_penalty_modifier_and_main_trade_node_draft.md`

```
# R15 results - The away-penalty modifier and the main trade node (side questions of R02)
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
(use only the facts and rows above; per row or group: consistent or not, with arithmetic; list every failure)
## 5. Unknowns, contradictions between sources, and what would settle them
## 6. Sources (ranked, one line on reliability each)
```
