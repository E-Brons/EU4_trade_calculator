# R10 request 1 - Embargo, privateers/pirates, node total vs sum of val

**Read first (by path, same folder; paste them in if you cannot read the repository):** `R10_embargo_privateers_transfers_misc_goal.md` (question, project context, data tables, rules, required format), `R10_embargo_privateers_transfers_misc_draft.md` (the first answer, which this request corrects).

**Rules (same as the goal):** every claim needs a source (URL or game file + line) and a **verbatim quote** from that source, and a confidence `confirmed|reported|inferred`. If you cannot establish something, write `UNKNOWN`; never fill a gap with a plausible guess. Do not invent quotes, file paths, defines or save rows. Where you test a formula, use only rows that appear in the goal's data tables and show the arithmetic. Verified facts listed in the goal are ground truth; if a source disagrees with them, say so instead of bending the formula.

**How to answer:** a file `R10_embargo_privateers_transfers_misc_response_1.md`. Answer only the numbered points below, keep their numbers (`Q1`, `Q2`, ...), and for each use the goal's claim format (Claim / Formula / Applies when / Source / Quote / Confidence / Caveats). Add at the end an updated list of what is still `UNKNOWN` and what would settle it.

## What was wrong with the draft (summary)

The draft's validation is circular: it defines `pirate_power = node.total - sum(val)` and then "reproduces" the gap with the same subtraction, so nothing was tested. It does not say whether pirate power is inside `retain_power`/`pull_power`, it ignores the TUR embargo case, gives an embargo formula with no source, and the goal's second table contradicts its claim C-02.

## Points to answer

**Q1 - Independent test of the pirate-power hypothesis.** The hypothesis is that `total - sum(val)` equals privateer power. Test it against something that does not use that subtraction. Possible independent checks: privateer power computed from `light_ship`/`ship_power` of pirate-flagged entries and `PIRATES_TRADE_POWER_FACTOR`; or `total` vs `collector_power_including_pirates`. If no such check is possible with the goal's tables, state `UNKNOWN` and list which save fields would be needed.

**Q2 - Contradicting data.** In the goal's second table, 14 of 15 rows have `collector_power == collector_power_including_pirates` and `total == sum(val)` although `num_collectors_including_pirates = num_collectors + 1` (only `girin` has a total gap, 438.463 vs 437.256). Explain what the extra collector is if it adds no power (a `PIR` entry with `val` 0? a country with zero power?), and what the real definition of `num_collectors_including_pirates` is. Do not state "+1 when privateer power > 0" unless a source says so verbatim.

**Q3 - Pirates in `retain_power` and `pull_power`.** Is privateer power part of `retain_power` and/or `pull_power`? The goal's verified fact is `retain_power = sum over collecting countries of (val - t_out + t_in)` (exact in 5,588 node instances), which has no pirate term. Say whether this fact already answers the question (pirates are not in `retain_power`), and what the evidence for `pull_power` is. Quote the source.

**Q4 - What are the 2% gaps, then?** The first table lists nodes where `total` exceeds sum(val) by more than 2% (e.g. sevilla 37.939, persia 28.859) and the `PIR` entry has no `val`. Give the cause with a source: (a) pirate power, (b) countries present in the node but without a listed entry, (c) something else. For `girin`, a node with a small gap but no matching pirate difference, state what explains it.

**Q5 - Embargo, with a source.** Give the embargo rule with a quoted source for each constant (`EMBARGO_BASE_EFFICIENCY = 0.5`, `EMBARGO_MERCANTILISM_EFFICIENCY = 50`, `embargo_efficiency`). The draft's formula multiplies by a "relative power share" with no source; either source it verbatim or remove it. State whether the embargo acts on `max_demand`, on `val`, or only on `money`, and how that can be told from a save.

**Q6 - The TUR case.** TUR has `trade_embargoed_by = [HUN, HAB, LUN, RUS, BNG, DEC]` and no embargoes of its own. Say what the rule predicts for TUR's `max_demand` in a node where several of these embargoers have power, and whether more than one embargoer stack (additively, multiplicatively, capped). If the goal's tables do not contain TUR node rows, say so and name the exact fields to extract so we can test it.

**Q7 - Other node-level effects.** For monopoly bonus, trade company region, blockade and treasure fleets, give only effects that you can source verbatim, and for each the save field where it shows. Remove from the answer any statement such as "+0.5 goods produced" or "up to -100% blockade" that you cannot quote; list it as `UNKNOWN` instead.
