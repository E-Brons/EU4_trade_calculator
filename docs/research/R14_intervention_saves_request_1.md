# R14 request 1 - Intervention-pair saves

**Read first (by path, same folder; paste them in if you cannot read the repository):** `R14_intervention_saves_goal.md` (question, project context, data tables, rules, required format), `R14_intervention_saves_draft.md` (the first answer, which this request corrects).

**Rules (same as the goal):** every claim needs a source (URL or game file + line) and a **verbatim quote** from that source, and a confidence `confirmed|reported|inferred`. If you cannot establish something, write `UNKNOWN`; never fill a gap with a plausible guess. Do not invent quotes, file paths, defines or save rows. Where you test a formula, use only rows that appear in the goal's data tables and show the arithmetic. Verified facts listed in the goal are ground truth; if a source disagrees with them, say so instead of bending the formula.

**How to answer:** a file `R14_intervention_saves_response_1.md`. Answer only the numbered points below, keep their numbers (`Q1`, `Q2`, ...), and for each use the goal's claim format (Claim / Formula / Applies when / Source / Quote / Confidence / Caveats). Add at the end an updated list of what is still `UNKNOWN` and what would settle it.

## What was wrong with the draft (summary)

The draft's matrix has factual errors: IV-01 uses FRA with `english_channel` as its home node, while IV-14 uses FRA with `champagne` (they cannot both be FRA's home node); IV-18 uses PRU, which does not exist in 1444; IV-02/03/07 treat the away penalty as -0.5 on `max_demand`, but our integration of R02 uses x 0.5 (a multiplier); IV-12 says ships change `prev`, which contradicts R11 and our data (ships do not propagate); the A-save date `1444.12.01` conflicts with the start column `1444.11.11`. It is missing the cases inland ships, embargo off and transfer off, and for each pair the control design, what to record, the determinism check and the one-line checklist.

## Points to answer

**Q1 - Correct the matrix.** Re-issue the full table (about 20 pairs) fixing: IV-01 (use a country whose home trade node is the node you name; give the node and the evidence; resolve the FRA conflict with IV-14), IV-18 (a country that exists at the chosen start date and can move its main trade port, and the target node), IV-12 (state that ship power does not propagate to `prev`; the expected change is only `ship_power` and `max_pow`), and the date columns (A-save date must follow from the start date; choose one convention and use it consistently). For every row verify the country exists, owns/has access to the node, has the needed merchant/ships at that start.

**Q2 - Away penalty.** The expected change for IV-02, IV-03 and IV-07 is written as "`max_demand` drops by 0.5". Our model (R02) multiplies `max_demand` by 0.5. Write the expected change as both numbers a reviewer will see in the saves (value before, value after) for each hypothesis, so the pair discriminates additive from multiplicative, and name the define (`TRADE_NON_CAPITAL_OFFICE`) with a quote.

**Q3 - Missing cases.** Add pairs for: ships assigned to an inland node (expected: impossible; say what the game shows and what to record), embargo turned off (reverse of IV-15), and transfer of trade power turned off (reverse of IV-16). Keep the total near 20 by merging redundant ones and say which you merged.

**Q4 - Per pair details.** For each pair give: (a) the start save/bookmark and country, (b) the exact in-game steps (UI path or console command, and the date to save), (c) the control design (what C does, how long), (d) the saved fields that must change in B vs C and by how much if the model is right, (e) the fields that must NOT change, (f) what to record in a notes file (date, tag, node, numbers seen in the UI). The draft's table has only (a), (b) and (d).

**Q5 - Determinism and divergence.** Answer with evidence: are B and C deterministic given the same A (random seed in the save, `ai` decisions, events, `random` in the monthly tick)? Which events can differ between B and C? Give a concrete divergence check using saved fields of unrelated nodes (the draft names `beijing`, `malacca`, `peru`, `zambezi`, `monomotapa`; check these are distant from the intervention nodes and from each other, and give the fields and tolerances). If the answer is `UNKNOWN`, propose the cheapest experiment (e.g. two C saves from the same A) to settle it.

**Q6 - Naming and checklist.** The draft's file naming `P<ID>_<TAG>_<YYYY>.<MM>.<DD>_<TYPE>.eu4` must fit our convention `Pxx_TAG_<date>_{A|C|B}.eu4`. Confirm the examples follow it. Add the one-line checklist for the person making the saves (non-Ironman, no mods, patch 1.37.5, save immediately after the tick, change exactly one thing, advance the same number of days, ...).

**Q7 - Quotes.** The draft's claims C-02 and C-03 quote `PLACED_MERCHANT_POWER = 2.0` and "first merchant adds +5%, diminishing to 5 merchants" without URL/line. Give the file and line or URL, or mark `UNKNOWN`. Also fix the variable `HOME_TRADE_BOOK_BONUS` whose path names `CAPITAL_NODE_POWER_BONUS` (one id), and `VAL_TRANSFER_BONUS` (check the define exists).
