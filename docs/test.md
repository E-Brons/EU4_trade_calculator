> **Superseded 2026-10-09.** This file describes how the removed player-centric engine (`app/engine`,
> `parsing/save.py`) was checked. The calculation is now `backend/app/trade/calc.py`, verified stage by stage and end
> to end against every clean dataset save: see `docs/trade_testing.md`. Kept for its history and findings.

> **Superseded (2026-10-06).** The fixture corpus this file describes (`backend/tests/fixtures/saves*`, `test_real_saves.py`) was removed in the data redesign: most of those saves were game-start or mid-month saves, which cannot test the calculation (see `docs/research/data_audit.md`). Current testing: `docs/trade_testing.md`; data: `datasets/eu4/`; experiments: `docs/research/experiments.md`.

# Testing the trade value calculation

This describes how to check `backend/app/engine/simulate.py` (and the save
parsing that feeds it, `backend/app/parsing/save.py`) against the actual
game, using real save files as ground truth -- not hand-derived numbers.

**Read the "Critical finding" section below before trusting the trade
model as-is.** Building this suite surfaced a real, confirmed accuracy bug
in the current model, on top of the automated tests it adds.

## 1. Ground truth: what a save already tells us

A `.eu4` save's `trade={ node={...} }` block is the game's own record of
that exact tick's trade state. Per node it includes (see
`backend/scripts/inspect_save.py` to dump one node's raw fields for
yourself):

- `local_value` -- that node's own production value.
- `total` -- **not** a ducat figure; it's `sum(top_power_values)`, a
  trade-power-weighted "reach" metric (see the Critical Finding below).
- `current` -- the actual ducat-scale value of the node, the one real
  income is computed from.
- `retention` -- fraction of the node retained locally vs. forwarded.
- `incoming` -- list of `{value, from, add}` per upstream link actually
  received this tick (present on nodes with upstream traffic).
- per-country sub-blocks (keyed by tag, e.g. `TUR={...}`): `val` (share of
  `total`), `total` (that country's share of `current`, i.e. their
  retained ducat value -- confusingly the same field name as the node's,
  a different quantity), `money` (their actual realized ducats/month there
  -- present only for collectors), `power_fraction`, `province_power`,
  `ship_power`, `has_trader`, `type` (Steer marker), `has_capital`.

Every test in this suite compares the simulator against these numbers
directly, not against independently-guessed expectations.

## 2. Critical finding: node value uses the wrong field (fixed) -- and a second bug found alongside it

**Update: both of the below are now fixed in `save.py`, confirmed against
35 real 1444.11.11 saves (2,695 node-country data points). This section is
kept as a record of what was wrong and how it was found -- see section 2c
for what's still open.**

### 2a. `current` is the node's *retained* ducat value, not `total`

`total` (`ParsedNode.total_value`) is `sum(top_power_values)` -- a
power-weighted reach/coloring statistic, **not ducats**. It's still used
for the `val`-sum and `retention` identity checks below (those are
power-domain identities, correct as-is), but it was also being used as if
it were the node's ducat value, which overstates it by up to ~15x.

The actual ducat-scale quantity is `current`, and its exact formula is now
confirmed to <0.001 absolute error across a full 80-node save:

```
current = (local_value + sum(incoming[].value)) * retention
```

i.e. `current` is the **retained** (post-forward) value -- gross value
entering the node, minus whatever gets forwarded downstream -- not the
gross value itself. (An earlier version of this finding treated `current`
as the gross value; that only looked right because it was checked against
an end node, where gross and retained are the same thing by construction --
nowhere for anything to be forwarded to.) `ParsedNode.current_value` now
carries this field, and `test_simulator_reproduces_saves_own_numbers`
compares the simulator's own `total_value - forwarded_value` (its retained
portion) against it, not `total_value` directly.

Per-country: `money = (current * power_fraction) * (1 + trade_efficiency +
merchant_present_bonus)`, and `power_fraction * current` is exactly the
per-country `total` field (confirmed exactly at Constantinople, Ragusa,
Venice in the original investigation, and broadly since).

### 2b. `has_trader` does not mean "collecting" without `has_capital` (fixed)

`build_node_states_from_save` used to treat any `has_trader=yes` country
with no `type` key as an active collector, same as a `has_capital` country.
**Confirmed false, at scale:** across all 2,695 real trade-node entries with
`power_fraction` present in the 35-save 1444 batch, `has_capital` was true
in every single one -- zero exceptions. Checked the other direction too:
1,330 entries have `has_trader=yes`, no capital, and aren't steering
either, and *none* of them carry a `power_fraction`/`money`/per-country
`total`. Whatever a bare `has_trader` flag means away from home, it isn't
"this country collects money here" -- at least not at these opening-state
saves, where nobody (player or AI) has yet made an explicit away-from-home
Collect assignment. `save.py` now only counts `has_capital` as "this other
country collects here"; a `has_trader`-only entry is treated as passive.

This fix alone took the real-save total-income accuracy from off by
10-15x (the `total`-vs-`current` confusion) to a median ~9% error across
the 35-save batch, with several saves under 2%. Per-node retained-value
error has a median of ~2% but a long tail of much worse outliers --
see 2c.

### 2c. Still open: what exactly counts as "retained power" at a mid-chain node

The two fixes above nail the *ducat conversion* (current = retained
gross value; who gets paid a share of it) wherever a save's own numbers
are being read directly. What's **not** yet solved is reconstructing the
retention *ratio* itself (how much of a node's gross value stays vs. gets
forwarded) from scratch for a hypothetical allocation -- needed for
what-if predictions, where there's no `current`/`retention` to just read
off a save.

### 2c. Solved for replaying a real save: `retain_power` and `pull_power`

Section 2b's fix stopped the engine from inventing phantom collectors, but
left open exactly how much of a node's value gets retained vs. forwarded at
an ordinary mid-chain node -- reconstructing that from country-level
classification (has_capital / is_steering / passive) turned out not to have
a clean closed-form answer (see the failed hypotheses below).

The actual answer: the save has two more node-level fields, `retain_power`
and `pull_power`, that were never parsed. **Confirmed exact** (<0.001
absolute error across all 3238 real node-instances with trade activity, in
all 50 saves):

```
retention = retain_power / (retain_power + pull_power)
```

`retain_power` also matches `sum(val)` over `has_capital` countries almost
exactly (a handful of New World/trade-company-region nodes are a confirmed
exception -- don't rely on that reconstruction, read the field directly).
`pull_power`'s own country-level composition was **not** solved -- tried
`sum(val)` over steering countries, over all non-capital countries, and a
few power-law/threshold variants (the `<2.0`-power propagation threshold
mentioned in `model.py`'s `Params` docstring is real and already-documented
there); best fit was R²=0.85, not exact. So `pull_power` can't be
reconstructed for a hypothetical allocation that was never actually
recorded in a save.

What this means in practice: `save.py` now also parses `retain_power`,
`pull_power`, and the exact `incoming` sum per node, and
`build_node_states_from_save` stores them on `NodeState` as `known_*`
fields together with the player's own recorded action. `simulate()` uses
them directly -- bypassing the approximate reconstruction entirely --
whenever the `Allocation` passed in is a byte-for-byte match for what was
actually recorded in the save (`NodeState.matches_recorded`). This is
exactly the case for `test_simulator_reproduces_saves_own_numbers`
(replaying the save's own allocation), and it takes real-save accuracy from
a many-x-off mismatch to **effectively exact**: per-node retained-value
error is 0.0 at the median across all 3789 checked node-instances (floating
point noise at the 99th percentile), and total-income error is under 1%
for 48 of 50 saves (worst two are tiny single-province economies where
0.001-ducat display rounding is a big fraction of the total -- see
`TOTAL_ABS_TOL` in `test_real_saves.py`).

For a genuinely hypothetical allocation (different from what any save
recorded -- the optimizer's actual job), `simulate()` falls through to the
old approximate reconstruction, unchanged from before. That's a real,
separate limitation, not fixed by the above -- solving it would need either
more targeted saves (explicit mixed Collect/Steer/nothing at the same node,
to isolate `pull_power`'s mechanic) or an external mechanics reference. The
"failed hypotheses" below are preserved as a record of what didn't work, in
case someone picks this up again:

- `has_capital`-only power as the retained pool: works if the node is a
  true end node (structurally always retention=1.0, nothing forwards to
  compute over), but badly undercounts retention at ordinary mid-chain
  nodes (e.g. `white_sea`: predicts ~0.23, actual 0.455).
- "Only power actually assigned to Steer is forwarded, everything else is
  retained": also wrong (predicts retention=1.0 at `white_sea` when nobody
  there is flagged `is_steering`, vs. the real 0.455 -- so unassigned,
  non-capital power *does* get forwarded by default a lot of the time,
  just not always).

`docs/imported/` corroborates the general DAG-propagation shape but has no
save-field-level specifics (doesn't even mention `val`/`current`/
`retain_power`/etc. by name) -- it's a generic design write-up, not derived
from inspecting real saves, so it couldn't and didn't resolve this.

**What's still confirmed correct regardless:** the two-term additive
income formula (`value_share * (1 + trade_efficiency +
merchant_present_bonus)`), `TRADE_MERCHANT_PRESENT` = 0.10, and the general
"value flows through a DAG, split by power, minus retention" shape of the
model. What's still approximate is reconstructing the retention split from
scratch for a node the player doesn't have direct save data for (i.e. a
true what-if prediction).

## 3. Save protocol

Non-Ironman saves need zero melting -- `.eu4` files from a regular game
save directly as plain text, so this is all local, no pdx.tools
round-trip needed.

**Every fixture in this suite is the game's opening state for one (date,
country) pair -- nothing else.** No merchant placement, steer target, or
ship count to set up by hand, and nothing that could drift between "what
the tester actually did" and "what the manifest says happened": the save
is made the instant the game starts, before a single tick passes.

For **every** save below:

- Single player, **Ironman off**, no console commands, no mods, patch
  1.37.x (matches `data/tradenodes.json`; regenerate it via
  `scripts/build_tradenodes.py` first if you're on a different patch).
- New game -> **historical setup** (not random new world) -> set the
  start date to the one in the table -> pick the country -> Play.
- **Do not unpause. Do not click anything.** Immediately open the menu and
  save (Esc -> Save Game). This is the entire "recipe" -- there is no
  merchant/ship change to make for any entry in the list below.
- Rename the file to match the `file` column in
  `backend/tests/fixtures/saves/saves.json` and drop it in that directory.
  After adding one, run `python3 scripts/zip_fixture_saves.py <id>` to add
  its tracked, compressed copy (see "Tracking the fixture saves" below).
- For exotic non-European tags: check that the tag in-game still matches
  the manifest's `tag` (some may have changed across patches/DLC) --
  `test_save_matches_manifest` will tell you immediately if it doesn't.

### Tracking the fixture saves

The raw saves are ~2.8GB total, and don't compress well as one blob (a
mixed-content archive doesn't hit the same ratio as the mostly-repetitive
text within a single save) -- so the raw `.eu4` files themselves stay
**gitignored**, but a small single-file zip of each (~13x smaller, plain
Clausewitz text compresses very well) lives in
`backend/tests/fixtures/saves_zip/` and **is tracked** (255MB total).
`test_real_saves.py` unzips one at a time, on demand, into pytest's
per-test `tmp_path` whenever the raw file isn't already sitting in
`fixtures/saves/` -- nothing is ever extracted into the repo itself, so a
fresh clone stays small on disk regardless of how many saves are in the
manifest. `scripts/zip_fixture_saves.py` (re-)generates the zips; run it
with no arguments to refresh everything, or pass specific ids after adding
a new save.

An opening-state save may not have `money` populated at all for any node
(no monthly trade tick has run yet). That's expected: the income-dependent
checks (`test_trade_efficiency_consistent_across_collecting_nodes`,
`test_simulator_reproduces_saves_own_numbers`) skip in that case, and the
structural checks (val sums, retention, manifest match) still run. If your
game client *does* populate `money` on the opening save (behavior can
differ by patch), that's a bonus, not a requirement -- don't unpause to
try to force it.

**Update, confirmed against real saves (S01-S07):** opening-state saves
*do* already have `money` populated -- the historical bookmark bakes in a
completed trade tick, not a blank one. So in practice you should see the
income-dependent checks run, not skip, on every save. The paragraph above
is left as a fallback in case that turns out to differ by patch/DLC --
don't unpause to chase `money` if it's genuinely missing on yours.

### 3B. The 19th century has no bookmark -- "hands-off" saves instead

Vanilla EU4's latest bookmark is 1785; the timeline ends at 1821 but there's
no historical-setup start point in between. For the 19th-century entries in
the table below (S67-S74), there's no way to get a true zero-tick opening
state -- instead:

- Start historical setup at the **1785** bookmark, pick the country, Play.
- **Take no action of any kind** -- no merchant/ship changes, no war, no
  diplomacy, nothing. Just unpause and let the clock run (you can freely
  change game *speed*, that's not a "change" in the relevant sense).
- Pause the instant you hit the target date in the table and save
  immediately.

This is not an opening state -- AI nations act, wars happen, institutions
spread -- so it's not bit-for-bit reproducible the way the other saves are.
But the player made zero decisions, which is the property that actually
matters here: nothing about the save's trade state was *set up* by hand for
a specific test to pass, it's just "whatever the world naturally looks like
at that date." The tests still only ever compare the simulator against
whatever that save actually contains, never against a hand-derived
expectation, so this is still real ground truth -- just a noisier sample
than the other categories (multi-decade AI divergence, not a controlled
formula check at t=0).

### Save list

**A -- 1444.11.11 grand campaign (broad graph coverage, one save per
country, nothing else varies):**

| ID | Country | Covers |
|----|---|---|
| S01 | Venice VEN | end node (venice) |
| S02 | England ENG | English Channel, sea node with a big starting fleet |
| S03 | France FRA | inland, several outgoing links |
| S04 | Castile CAS | Sevilla, coastal node mid-chain |
| S05 | Portugal POR | Atlantic coast / Sevilla region |
| S06 | Austria HAB | Wien, inland, 3 outgoing links |
| S07 | Burgundy BUR | Antwerp end node |
| S08 | Lübeck LUB | Lübeck / Baltic |
| S09 | Genoa GEN | Genoa end node |
| S10 | Ragusa RAG | small player power, node with many links |
| S11 | Poland POL | Krakow, inland |
| S12 | Novgorod NOV | Novgorod |
| S13 | Sweden SWE | Baltic Sea |
| S14 | Ottomans TUR | Constantinople -- the original hand-verification region (`simulate.py`'s docstring) |
| S15 | Mamluks MAM | Alexandria |
| S16 | Timurids TIM | Persia, Central Asian hub, 2 outgoing |
| S17 | Muscovy MOS | Novgorod/Kazan region |
| S18 | Kazan KAZ | Kazan, Volga region |
| S19 | Crimea CRI | Crimea |
| S20 | Ming MNG | Beijing, East Asia land route |
| S21 | Ashikaga JAP | Nippon, island end-of-chain node |
| S22 | Joseon KOR | Girin, shared node with China/Japan |
| S23 | Vijayanagar VIJ | Comorin Cape, India multi-link hub |
| S24 | Bahmanis BAH | Gujarat, India west coast |
| S25 | Delhi DLH | Doab, inland India |
| S26 | Ayutthaya AYU | Gulf of Siam, mainland SE Asia |
| S27 | Majapahit MAJ | Malacca, maritime SE Asia chokepoint |
| S28 | Ethiopia ETH | inland Horn of Africa |
| S29 | Mali MLI | Timbuktu, West Africa |
| S30 | Kongo KON | Central Africa |
| S31 | Great Zimbabwe ZIM | Zambezi, Southern Africa |
| S32 | Katsina KTS | isolated source node, no incoming edges |
| S33 | Aztecs AZT | Mexico, New World |
| S34 | Inca INC | Lima, isolated New World source node |
| S35 | Iroquois IRO | St. Lawrence / James Bay, North America |

**B -- later historical-setup start dates (same handful of regions, later
bookmarks -- checks whether tech/institutions/ideas/trade companies change
the formula, not just the numbers):**

| ID | Date | Country |
|----|---|---|
| S36 | 1500.1.1 | Ottomans TUR |
| S37 | 1600.1.1 | Ottomans TUR |
| S38 | 1700.1.1 | Ottomans TUR |
| S39 | 1550.1.1 | Spain SPA |
| S40 | 1600.1.1 | Portugal POR |
| S41 | 1650.1.1 | Netherlands NED |
| S42 | 1750.1.1 | Great Britain GBR |

**C -- 16th century (1526 / 1550 bookmarks).** A couple of these repeat
S01/S02/S09's hub countries at a later bookmark (Venice/English
Channel/Genoa see the most competing merchants of any node, so more eras of
data there is worth more than another single-country node); the rest fill
previously-untouched nodes/regions:

| ID | Date | Country | Covers |
|----|---|---|---|
| S43 | 1526.1.1 | England ENG | English Channel hub, 2nd era |
| S44 | 1550.1.1 | Genoa GEN | Genoa hub, 2nd era |
| S45 | 1526.1.1 | Mughals MUG | Lahore, India -- new node |
| S46 | 1526.1.1 | Safavid Persia PER | Persia hub, Shia gunpowder empire (vs. S16's Timurids) |
| S47 | 1550.1.1 | Songhai SON | Timbuktu, West Africa (different government than S29's Mali) |
| S48 | 1526.1.1 | Bukhara BUK | Samarkand, Central Asia -- new node |
| S49 | 1550.1.1 | Hafsid Tunis TUN | Tunis, Barbary Coast -- new node |
| S50 | 1550.1.1 | Joseon KOR | Girin hub, 2nd era |

**D -- 17th century (originally planned as the 1600 / 1630 / 1650 bookmarks;
actual dates below are whatever was actually collected, updated in the
manifest -- close enough to the original intent, not worth remaking):**

| ID | Date | Country | Covers |
|----|---|---|---|
| S51 | 1600.1.1 | Venice VEN | Venice hub, 3rd era |
| S52 | 1644.11.11 | England ENG | English Channel hub, Commonwealth era |
| S53 | 1624.11.11 | Netherlands NED | newly-independent Dutch Republic (earlier era than S41) |
| S54 | 1614.11.11 | Russia RUS | Novgorod, Tsardom-era government reform (vs. S12/S17's Novgorod/Muscovy) |
| S55 | 1634.11.11 | Ming MNG | Beijing hub, late-Ming era (vs. S20's 1444) |
| S56 | 1650.11.11 | Kongo KON | Central Africa, 2nd era (Christianized government) |
| S57 | 1650.11.11 | Oman OMA | Persian Gulf/Hormuz region -- new node |
| S58 | 1630.11.11 | Bijapur BIJ | Deccan, India -- new node |

**E -- 18th century (originally planned as 1700 / 1739 / 1761 / 1785):**

| ID | Date | Country | Covers |
|----|---|---|---|
| S59 | 1700.1.11 | Genoa GEN | Genoa hub, 3rd era |
| S60 | 1700.1.11 | Venice VEN | Venice hub, 4th era (ended up close to S59's date -- the two Venice slots collapsed to one era, see S51 above) |
| S61 | 1700.11.11 | Russia RUS | Novgorod, Petrine Westernizing reforms (vs. S54's 1614) |
| S62 | 1744.11.11 | Prussia PRU | Saxony/Baltic region -- new node |
| S63 | 1744.11.11 | Qing QNG | Beijing hub, Qing era (vs. S20/S55's Ming) |
| S64 | 1761.1.11 | Mysore MYS | Deccan/South India, 2nd era (vs. S58's Bijapur) |
| S65 | 1785.1.11 | Oman OMA | Persian Gulf/Zanzibar, 2nd era (vs. S57's 1650) |
| S66 | 1785.1.11 | United States USA | Chesapeake Bay, New World republic -- new node and new government type |

**F -- 19th century (hands-off runs from a late-1700s bookmark -- see section
3B above, not opening states; originally planned as 1800-1821):**

| ID | Date | Country | Covers |
|----|---|---|---|
| S67 | 1800.1.11 | Great Britain GBR | English Channel hub, Industrial Revolution era |
| S68 | 1810.1.11 | Russia RUS | Novgorod, Napoleonic era (vs. S61's 1700) |
| S69 | 1800.1.11 | France FRA | Revolutionary/Napoleonic France -- major government/institution shift |
| S70 | 1810.1.11 | Austria HAB | Wien, Napoleonic Wars era |
| S71 | 1820.1.11 | Qing QNG | Beijing hub, end-date China (vs. S63's 1744) |
| S72 | 1821.1.1 | United States USA | Chesapeake Bay, growing USA (vs. S66's 1785) |
| S73 | 1821.1.1 | Ottomans TUR | Constantinople, end-date -- completes the S14/S36/S37/S38 longitudinal arc |
| S74 | 1821.1.1 | Oman OMA | Persian Gulf/Zanzibar, end-date (vs. S57/S65) |

**S51 was filled in later** -- initially not made (the first Venice save
collected beyond S01 landed at 1700.1.11 and was used for S60 instead, a
better fit for "4th era" than a 100-year gap from S01 would've been for
"3rd era"), then a dedicated 1600.1.1 Venice save was added, restoring the
originally-planned 4 eras of Venice data (S01/S51/S60, plus the neighboring
Genoa hub at S09/S44/S59).

The tags in C-F for anything past the well-known majors (Mughals, Songhai,
Bukhara, Tunis, Oman, Bijapur, Qing, Mysore) are a best guess at what's
actually selectable in your client's bookmark country list, same caveat as
the exotic tags in table A -- `test_save_matches_manifest` will tell you
immediately if a guess was wrong.

**G -- sprawling colonial empires (mid-18th century, 1744.11.11): a single
country present across dozens of nodes at once**, not just its home region.
Every save above is a fresh 1444/bookmark opening state where a country is
realistically present in a handful of nodes; these instead pick major
colonial powers well into their empire-building, exercising the val-sum/
retention checks across a much larger slice of the 80-node graph per save
(confirmed: FRA present in 23 nodes, NED 22, POR 19, SPA 12 -- vs. 1-3 for
a typical table A/B/C save) even though, like every other save here, only
the home node actively collects (still a pure opening state, no merchant
placement):

| ID | Date | Country | Covers |
|----|---|---|---|
| S75 | 1744.11.11 | France FRA | Champagne hub, 23-node colonial reach |
| S76 | 1744.11.11 | Netherlands NED | English Channel hub, 22-node colonial reach |
| S77 | 1744.11.11 | Portugal POR | Sevilla hub, 19-node colonial reach |
| S78 | 1744.11.11 | Spain SPA | Sevilla hub, 12-node colonial reach |

Great Britain was considered too but skipped -- already well covered
across eras by S42/S67 (and GBR's reach is a similar story to NED's, both
English Channel-based).

The "Covers" column is only there to explain why a case is included -- the
tests never assert it, only `tag` and `date` (and that a home node
resolves at all).


## 4. Running it

```bash
cd backend
pytest tests/test_real_saves.py -v      # skips any save you haven't made yet
python3 scripts/compare_save.py tests/fixtures/saves/S14_TUR_1444.11.11.eu4
```

`compare_save.py` prints a node-by-node table (save vs. simulated total,
`sum(val)`, income, retention) sorted by error size -- start there when a
test fails.

## 5. What each check means

From `backend/tests/test_real_saves.py`:

1. **`test_save_matches_manifest`** -- the save is actually the (date,
   country) opening state the manifest says it is, and its home node
   resolved to something in the trade graph. Catches a botched save (wrong
   country, wrong date, or a capital the parser couldn't place) before
   it's mistaken for a model bug.
2. **`test_val_sums_to_node_total`** -- accounting identity, should almost
   always hold closely; a failure here can mean the save parsing itself is
   broken (wrong node, wrong tag regex, truncated block). In practice the
   tolerance is deliberately generous (25%): 99% of the 3965 checked
   node-instances are within 0.2% (save-side display rounding on nodes with
   many participants), but a small number (18, concentrated in
   fragmented-minor-state regions like `hormuz` at the 1500 bookmark) are
   off by much more -- investigated, and the gap matches this suite's
   already out-of-scope privateers/piracy exclusion (the save has separate
   `..._including_pirates` fields never parsed here), not a parsing bug.
   Doesn't affect income accuracy -- see (5).
3. **`test_retention_matches_retain_power_share`** -- now a pure accounting
   identity read directly from the save (`retain_power`/`pull_power`, see
   section 2c) -- should always hold to <0.5%, no reconstruction involved.
4. **`test_trade_efficiency_consistent_across_collecting_nodes`** -- the
   country's trade efficiency should back-solve to the same value at every
   node it collects at; a large spread flags a save with mixed
   circumstances or a parsing bug. Skipped if the save has fewer than 2
   collecting nodes (expected for an opening-state save before the first
   trade tick, or for a country that starts with no merchant assigned).
5. **`test_simulator_reproduces_saves_own_numbers`** -- the real accuracy
   check, and now passing across all 50 saves. Section 2c's `retain_power`/
   `pull_power` fix (on top of 2a/2b) took real-save accuracy from a
   many-x-off mismatch to effectively exact when replaying a save's own
   recorded allocation: per-node retained-value error is 0.0 at the median
   (floating-point noise at the 99th percentile, across 3789 node-instances
   checked), and total-income error is under 1% for 48 of 50 saves (the
   other two are tiny single-province economies where display-scale
   rounding is a large fraction of a ~0.07-ducat total -- see
   `TOTAL_ABS_TOL`). Skipped for the same reason as (4) if there's no
   collecting node to back-solve trade efficiency from. Note this measures
   *replay* accuracy (reproducing what's already in a save) -- true what-if
   prediction accuracy (a hypothetical allocation, the optimizer's actual
   job) is a separate, still-approximate concern, see section 2c.

Known approximations that may still show small residual error even after
the `current`-fix above (see `model.py`'s `Params` docstring for the full
list, these are intentional, not bugs): splitting a multi-link node's
aggregate steer weight without per-country granularity; the <2.0-power
propagation-exclusion threshold (not modeled); per-light-ship power
variance for large fleets; even-split fallback when nobody at all steers
out of a node.

**What this suite deliberately does not cover:** predicting a
*different* allocation's income (the optimizer's actual job) against real
save ground truth -- that needs two saves of the same country that differ
only in merchant/ship placement, which is exactly the kind of
hard-to-reproduce-by-hand change this suite dropped in favor of pure
opening states (see the top of this file). That prediction path stays
covered by the hand-derived unit tests in `backend/tests/test_simulate.py`
instead.

## 6. Adding a save

Add an entry to `saves.json` (`id`, `file`, `tag`, `date`), drop the
`.eu4` file next to it, run `pytest tests/test_real_saves.py -v -k <id>`.
