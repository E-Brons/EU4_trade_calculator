# R11 request 1 - Ships and trade power

**Read first (by path, same folder; paste them in if you cannot read the repository):** `R11_ships_and_trade_power_goal.md` (question, project context, data tables, rules, required format), `R11_ships_and_trade_power_draft.md` (the first answer, which this request corrects).

**Rules (same as the goal):** every claim needs a source (URL or game file + line) and a **verbatim quote** from that source, and a confidence `confirmed|reported|inferred`. If you cannot establish something, write `UNKNOWN`; never fill a gap with a plausible guess. Do not invent quotes, file paths, defines or save rows. Where you test a formula, use only rows that appear in the goal's data tables and show the arithmetic. Verified facts listed in the goal are ground truth; if a source disagrees with them, say so instead of bending the formula.

**How to answer:** a file `R11_ships_and_trade_power_response_1.md`. Answer only the numbered points below, keep their numbers (`Q1`, `Q2`, ...), and for each use the goal's claim format (Claim / Formula / Applies when / Source / Quote / Confidence / Caveats). Add at the end an updated list of what is still `UNKNOWN` and what would settle it.

## What was wrong with the draft (summary)

The draft's fleet arithmetic is impossible: its six node rows need 67 early frigates (20+13+33+1), but the goal says TUR owns 66. It says `ship_power` already includes all modifiers, yet validates with bare base values; it does not explain the corpus maximum of 3.675 power per ship (above any base value it lists); it skips the per-node cap, 98 vs 100 ships, port/organisation limits, flagship and doctrine modifiers, how the assignment is stored, and the requested rule for one more ship. Its claim C-02 "quote" is copied from our own goal file.

## Points to answer

**Q1 - Fix the fleet arithmetic.** Reconcile the six node rows of the goal with TUR's fleet (early_frigate 66, frigate 34, plus the other types listed). The draft assigns 67 early frigates and 31 frigates; that is impossible. Find an assignment of the 100 light ships to the six rows (and 2 unassigned) that reproduces every `ship_power` exactly, and show it. Remember that `ship_power / light_ship` in the whole corpus ranges from 2.000 to 3.675, so some rows may involve other ship types or modifiers. If several assignments fit, say so and state `UNKNOWN`.

**Q2 - Which ships count as light ships.** TUR also owns galleys, galiots, galleasses, carracks, galleons, merchantmen and a war galley. Which of these have a `trade_power` value (give the file and line in `common/units`) and may be assigned to protect trade? Are those included in the "100 light ships" or not?

**Q3 - What produces 3.675 per ship?** The corpus maximum `ship_power / light_ship` is 3.675 (above the frigate's 3.5; 3.675 = 3.5 x 1.05). Give the modifier that can raise it (e.g. `global_ship_trade_power`, a naval idea, flagship), with a quoted source. Say, for each of `global_ship_trade_power`, `ship_trade_power_modifier`, `trade_power_in_fleet_modifier` and doctrines, whether it is inside the saved `ship_power`. The draft's formula contains a `light_ship_efficiency_factor` that appears in no source; quote it or remove it.

**Q4 - Limits.** Give, with quotes: whether `TRADE_SHIP_MAX_DAYS_IN_PORT`/`TRADE_SHIP_ORG_LIMIT` reduce `ship_power` (and by what rule, step or linear), whether ships in port or in combat count, whether there is a cap on ships per node (the goal says Malacca has 24, Venice 36), and why 98 of 100 ships are assigned (TUR `num_ships_protecting_trade`).

**Q5 - Storage of the assignment.** The draft claims fleets are stored in a country `fleet = { mission = protect_trade target = <node_id> }` block. Give a source (a parser project such as pdx-tools/eu4save/rakaly, or a save excerpt) or write `UNKNOWN`. Say which field a calculator must read to move ships between nodes.

**Q6 - The rule for one more ship.** State the exact rule for how much `ship_power` (and `max_pow`) one additional ship of a given type adds at a node for a given country, as a function of the saved fields (`ship_power`, `light_ship`, `max_demand`, ...). Mark which parts are `confirmed` and which `UNKNOWN`.

**Q7 - Open sea vs coastal.** The draft says `OPEN_SEA_MODIFIER`/`COASTAL_MODIFIER` do not affect trade power. Give the source for what they do affect, with a quote; otherwise mark it `UNKNOWN`. The goal's rows are all "coastal"; say whether any evidence exists for or against an open-sea effect.

**Q8 - Remove the copied quote.** The draft's C-02 quote ("Per-country-in-node fields in the save: ship_power + light_ship ...") comes from our goal file, not from a source. Replace it with a real source or mark the claim `inferred`.
