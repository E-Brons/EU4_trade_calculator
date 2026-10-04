# R13 request 1 - Province trade power and local value

**Read first (by path, same folder; paste them in if you cannot read the repository):** `R13_province_trade_power_goal.md` (question, project context, data tables, rules, required format), `R13_province_trade_power_draft.md` (the first answer, which this request corrects).

**Rules (same as the goal):** every claim needs a source (URL or game file + line) and a **verbatim quote** from that source, and a confidence `confirmed|reported|inferred`. If you cannot establish something, write `UNKNOWN`; never fill a gap with a plausible guess. Do not invent quotes, file paths, defines or save rows. Where you test a formula, use only rows that appear in the goal's data tables and show the arithmetic. Verified facts listed in the goal are ground truth; if a source disagrees with them, say so instead of bending the formula.

**How to answer:** a file `R13_province_trade_power_response_1.md`. Answer only the numbered points below, keep their numbers (`Q1`, `Q2`, ...), and for each use the goal's claim format (Claim / Formula / Applies when / Source / Quote / Confidence / Caveats). Add at the end an updated list of what is still `UNKNOWN` and what would settle it.

## What was wrong with the draft (summary)

The draft has no validation against real data: its four test cases are invented (including "matches save field trade_power = 34.125"). It states the monthly trade value formula both without and with a division by 12; computes caravan power as development x 3 (cap 50), which looks wrong; asserts but does not test that `province_power` is the sum of province `trade_power`; and omits goods size (`trade_goods_size`), trade company region and merchant republic effects.

## Points to answer

**Q1 - One trade value formula.** The draft's section 1 gives `Trade Value = goods x price x (1 + modifier)` and claim C-03 divides by 12. State which is right and in which unit `local_value` is stored (ducats per month). Give the full formula from goods produced, with the exact meaning of `trade_goods_size`, `trade_goods_size_modifier`, development by production, and quote a source. Check it against one real example if the goal contains one; if it does not, say `UNKNOWN` instead of inventing numbers.

**Q2 - Caravan power.** The draft sets caravan power = clamp(total development x `CARAVAN_FACTOR` (3.0), 2, 50). Verify against a quoted source (wiki or `common/defines.lua` line) what `CARAVAN_FACTOR`, `CARAVAN_POWER_MIN`, `CARAVAN_POWER_MAX` mean and what they multiply (the number of caravans? the trade power of the source nodes? development?). If you cannot confirm the formula, write `UNKNOWN`.

**Q3 - Is `province_power` the plain sum of the provinces' `trade_power`?** This is the goal's question (3). Say whether any source states it, and whether it holds for the provinces whose owner is in a trade company, or occupied or blockaded. Describe the test that settles it with the 80 saves (which two fields to compare, the tolerance), without claiming it was run unless you ran it.

**Q4 - Province trade power: what is included in the saved `trade_power`.** Give a quoted source for each of: development x 0.2, centers of trade (+5/+10/+25 by level), estuary/harbor, coastal +25%, buildings, trade company +100%, autonomy, `global_prov_trade_power_modifier` (mercantilism). Mark each `confirmed`, `reported`, `inferred`. The draft says mercantilism gives +2% per point; quote the line that states the scale, or write `UNKNOWN`. State whether the order is `base x (1 + local) x (1 + global)` or `base x (1 + local + global)`, with a source.

**Q5 - Replace the invented test cases.** Remove the four invented cases. If the goal data contains a province with its inputs and the stored `trade_power=41.670`, use it; otherwise state clearly that no real validation is possible from this task, and list the fields that would be needed (development, coastal flag, buildings, CoT level, autonomy, owner modifiers).

**Q6 - Missing effects.** Give, with sources, the effect on node power and value of: trade company region (the 50% rule and what is added), merchant republic bonus, blockade (the exact scale), occupation/siege, and the trade company goods produced bonus (draft section 5 claims it scales with the TC share of node power; quote it or write `UNKNOWN`).
