# R14 - Design of intervention-pair saves (counterfactual validation)

**How to use this file:** it is self-contained. Give it, unchanged, to an AI assistant that has internet access (web search/fetch). Save the assistant's final answer as `R14_intervention_saves_draft.md` in the same folder. Do not paste other files; everything needed is below.

## Project context (same in every task)

We are building a calculator for **Europa Universalis IV, game version 1.37.5** (80 trade nodes, 159 links, end nodes `english_channel`, `genua`, `venice`). It reads the `trade={ node={...} }` block of a save game and must reproduce the game's own trade numbers exactly (so we can also search the best merchant/ship assignment). The calculation must be an algorithm over variables **read from the save** plus constants from the game's files (`common/defines.lua` etc.). We validate against 80 real saves (78 game-start/hands-off snapshots, 2 played saves) which record every intermediate quantity per country per node. The game's trade formulas are compiled (not in script files), so we are reverse-engineering them from public sources plus the data tables below. We already verified these facts (usable as ground truth): `current = (local_value + sum(incoming.value)) * retention`; `outgoing = gross - current`; `retention = retain_power/(retain_power+pull_power)`; `val = max_pow * max_demand` for every country entry (max error 0.05%); `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in all 5,588 node instances); `total = sum of all val`; `prev` (power propagated in) is about `sum over downstream nodes D of province_power_D / 5` (95% of 519 entries within 1%).

Per-country-in-node fields in the save (our reading; confirm/correct only if your task asks): `province_power` (sum of the country's provinces' trade power there), `ship_power` + `light_ship` (assigned light ships), `prev` (propagated in), `max_pow` (= province+ship+prev+flat extras), `max_demand` (multiplier; `val = max_pow*max_demand`), `val` (effective power used for sharing), `t_in`/`t_out` (transferred power received/given; `t_from`/`t_to` map tag->amount), `potential`, `already_sent`, `has_capital`, `has_trader` (merchant present), `type` (key present = merchant is steering), `steer_power` (index of the outgoing link steered to; absent = first), `total` (key present = country is collecting; value = its share of retained ducats), `power_fraction`, `money` (monthly ducats; collectors only), `add` (steering value bonus), `modifier={key duration power power_modifier}`. Node fields: `local_value`, `incoming={add value from}` (`from` = 1-based index in the save's node list), `current`, `outgoing`, `value_added_outgoing`, `retention`, `retain_power`, `pull_power` (absent at end nodes), `steer_power` (one number per outgoing link, in graph edge order), `total`, `p_pow`, `max`, `highest_power`, `collector_power`, `collector_power_including_pirates`, `num_collectors(_including_pirates)`, `top_power(_values)`, `top_provinces(_values)`, `trade_company_region`.
The save does NOT store `trade_efficiency`, `global_trade_power` or any other aggregated country modifier (verified: 0 occurrences of those strings in a full save).

## Rules for your answer

1. Every claim needs a source (URL, or game file path + line) and a **verbatim quote**; give a confidence: `confirmed` (developer/wiki statement with numbers), `reported` (community claim backed by data), `inferred` (your reasoning). If you cannot establish something, write `UNKNOWN`. **Never fill a gap with a plausible guess.**
2. Test your proposed formula against the data tables in this file and report which rows it reproduces (show arithmetic for at least 5 rows) and which fail.
3. Prefer primary sources: Paradox developer diaries and patch notes, the Paradox wiki (eu4.paradoxwikis.com), Paradox forums, then reddit r/eu4, then GitHub projects that read the same save fields (pdx-tools/pdx-tools, rakaly, eu4save, EU4 trade calculators/simulators), then game files if quoted in sources.
4. Be explicit about the game version each source refers to; the trade system changed in patches 1.29/1.30 and later.

## Required format of `R14_intervention_saves_draft.md`

```
# R14 results - Design of intervention-pair saves (counterfactual validation)
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

Snapshots cannot prove what happens if the player **changes** merchants or ships, which is exactly what our optimizer predicts. We will create **intervention pairs** in the real game and compare. Design the minimum set (target about 20 pairs) that covers every case in the table below. For each pair give: id, country and start save (any historical start bookmark or an existing played save of ours may be used; non-Ironman, no mods, patch 1.37.5), exact in-game steps, which saved numbers should change and by how much if our model is right, the control design, and what to record.

Protocol we plan (improve it if you see flaws): **A** = save immediately after a monthly tick. **C** (control) = reload A, change nothing, advance to just after the next tick, save. **B** (intervention) = reload A, make exactly one change, advance the same number of days, save. The effect of the change is B minus C (AI actions are deterministic given the same save; check whether that is true and whether the random seed, `ai` decisions, or events can diverge between B and C; propose a way to detect divergence, for example comparing nodes unrelated to the intervention).

Cases to cover (each as one or more pairs): merchant none -> collect at the home node; merchant none -> collect at an away node (with and without existing province power there); merchant none -> steer toward each outgoing link (2-link and 3-link nodes); steer link A -> link B; collect -> steer; 2 merchants steering the same link (bonus per merchant); light ships +N at: the home node, a node where the player steers, a node where the player collects away, a passive foreign node, an inland node (should be impossible); ship type mix (barque vs frigate); recall a merchant (`merchant_recalled`); embargo on/off; transfer trade power on/off between two countries; a trade company region node; moving the capital; unlocking a trade-efficiency idea/policy (to measure `trade_efficiency` effect); a country with power below the propagation threshold 2.

Also give a naming scheme for the resulting fixture files that fits our convention `Pxx_TAG_<date>_{A|C|B}.eu4` and a one-line checklist for the person making the saves (so no step can be forgotten).
