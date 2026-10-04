# R12 request 1 - Monthly tick timing

**Read first (by path, same folder; paste them in if you cannot read the repository):** `R12_monthly_tick_timing_goal.md` (question, project context, data tables, rules, required format), `R12_monthly_tick_timing_draft.md` (the first answer, which this request corrects).

**Rules (same as the goal):** every claim needs a source (URL or game file + line) and a **verbatim quote** from that source, and a confidence `confirmed|reported|inferred`. If you cannot establish something, write `UNKNOWN`; never fill a gap with a plausible guess. Do not invent quotes, file paths, defines or save rows. Where you test a formula, use only rows that appear in the goal's data tables and show the arithmetic. Verified facts listed in the goal are ground truth; if a source disagrees with them, say so instead of bending the formula.

**How to answer:** a file `R12_monthly_tick_timing_response_1.md`. Answer only the numbered points below, keep their numbers (`Q1`, `Q2`, ...), and for each use the goal's claim format (Claim / Formula / Applies when / Source / Quote / Confidence / Caveats). Add at the end an updated list of what is still `UNKNOWN` and what would settle it.

## What was wrong with the draft (summary)

The draft explains the 4.5% of nodes where link values do not sum to `outgoing` by `value_added_outgoing != outgoing`, but the goal states that `value_added_outgoing` equals `outgoing` in those nodes, so the explanation contradicts the data. Its validation uses invented nodes A-E, not rows from the goal. It does not say on which day of the month country modifiers are updated, and its quotes and the define `NAV_PER_ADDED_SUB_NODE` could not be traced to a source.

## Points to answer

**Q1 - Explain the 4.5% mismatch without assuming what the data excludes.** In 95.5% of nodes `sum(downstream incoming.value) == outgoing` (median error 0); in the rest it differs by up to 7 ducats, and `value_added_outgoing == outgoing` there. Which mechanism makes the downstream link values differ from `outgoing`? Evaluate each candidate and say which is `confirmed`, `reported`, `inferred` or `UNKNOWN`: the steering bonus `add` (and where it is added: on the link, at the target), `trade_steering`/`TRADE_STEERING`-type modifiers, rounding/fixed-point truncation (3 decimals), values lagging by one tick, end-node or merchant-republic effects, a node whose link is steered to another node. Give a test that distinguishes them using only saved fields (say which fields).

**Q2 - What `value_added_outgoing` and `add` really are.** Give the source and a quote defining `value_added_outgoing` (node) and `add` (country in node, and `incoming.add`). The draft states `value_added_outgoing = outgoing x (1 + steering_bonus)` and "+5%, ... up to 5 merchants"; verify with a quote or remove it. Check against `R08_steering_and_link_split_draft.md` and state any contradiction.

**Q3 - Replace the invented validation.** The draft's "Nodes A-E" are not in any data. Redo the validation of `current = (local_value + sum(incoming)) * retention` using rows from the goal, or state that the goal contains no such rows. Do not present invented numbers as corpus results.

**Q4 - Day of the month and order.** Give a quoted source for: on which day trade power, value flow, `retention`, `money` and country modifiers are recomputed (daily, on the 1st, or at month end), and whether the order is power -> propagation -> classification -> value flow -> income. The draft states "on the 1st" and a 7-step order without a primary source; mark what is not sourced as `inferred` or `UNKNOWN`.

**Q5 - Played saves not on the 1st.** Two saves are dated 1665.4.22 and 1682.4.18. Say which inputs can have changed since the last tick (merchant placement, ships, ideas, diplomacy) and which saved fields would then be inconsistent with each other. Give a check, using saved fields only, that tells whether a save is internally consistent.

**Q6 - `prev` timing.** The draft quotes "20% ... calculated dynamically" for `prev`. Verify the quote at its URL. The goal's verified fact is `prev` about `sum over downstream nodes of province_power / 5`. State whether `prev` uses the current or the previous tick's province power, with evidence.

**Q7 - Unverifiable items.** Give the real name and file of the define you called `NAV_PER_ADDED_SUB_NODE` (namespace and line), or remove it. Remove or re-source the quotes attributed to the Paradox forums and developer diary if you cannot give a URL.
