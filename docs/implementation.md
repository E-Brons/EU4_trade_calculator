# Implementation

## Architecture

```
frontend/ (Flutter web)  --HTTP-->  backend/ (FastAPI)
                                       |
                                       +-- app/parsing/  save -> engine input
                                       +-- app/engine/   simulate + optimize
                                       +-- app/api.py    ties it together
```

The frontend never talks to the trade model directly; it POSTs node
states/params/allocations to the backend and renders whatever comes back.
This keeps the actual EU4 mechanics in one place (Python), testable with
plain pytest, independent of the UI.

## Trade node graph (`app/parsing/tradenodes.py`, `data/tradenodes.json`)

`data/tradenodes.json` is generated once (`scripts/build_tradenodes.py`)
from the game's own `common/tradenodes/00_tradenodes.txt` (parsed with
`clausewitz.py`, see below) plus English localisation, and committed --
the app doesn't need a local EU4 install to run. `TradeGraph` exposes the
80 nodes' outgoing edges, inland flag, and a topological order (Kahn's
algorithm over "sends value to" edges) that the simulator processes in.

## Clausewitz text-format parser (`app/parsing/clausewitz.py`)

A small tokenizer + recursive-descent parser for Paradox's `key=value` /
`key={...}` format, used both for the static game files and for melted
save text. A block is a dict if any top-level item inside it is a
`key=value` pair, otherwise a list of scalars. Duplicate keys at the same
level become a list, in first-seen order (needed for e.g. a node's
repeated `outgoing={...}` blocks, or a country's repeated `steer_power=`
values).

## Trade simulation (`app/engine/model.py`, `app/engine/simulate.py`)

`simulate()` processes nodes in topological (upstream-first) order.
Per node: `total_value = local_value + incoming`; power (the player's,
computed fresh each call from `Params`; everyone else's, fixed input from
`NodeState`) determines what fraction is retained (collected) vs.
forwarded down outgoing links, weighted by steering power where
explicit, split evenly among passive (no-merchant) power otherwise.

The formula was reverse-engineered against real `common/defines.lua`
constants and a real melted 1.37.5 save (see the module docstrings in
`model.py` and `simulate.py` for the full derivation with real numbers),
not tuned by guesswork:

- `TRADE_POWER_HOME_BONUS` (+10%) applies to power *added* at the home
  node, not the base (which already reflects it via the save's own
  `province_power`).
- `TRADE_MERCHANT_PRESENT` (+10%) is a separate, additive **income**
  bonus for collecting via an explicit merchant, at any node.
- `TRADE_CAPITAL_POWER` (5.0) vs. `MERCHANT_MAX_POWER_BONUS` (2.0): a
  merchant's power differs by home/away and the two don't stack.
- A once-assumed "-50% power away from home" penalty was tested against
  and **refuted** by real save data (a country collecting away from home
  showed *higher* effective power, not halved) and removed entirely.
- `trade_efficiency` genuinely cannot be derived from the trade block (an
  `add` field was suspected and refuted -- it only ever appears on
  steering entries, never collectors); it stays an explicit, editable
  `Params` field.

**"Current income" is not computed by this simulator at all when a save
is available** -- it's read directly from the save's own `money` field
(`ParsedSave.actual_current_income`), which the game has already
computed exactly. `simulate()`'s output is reserved for genuinely
hypothetical allocations, where no ground truth exists and an estimate is
unavoidable. Because that estimate's absolute scale runs a bit low
(mostly due to an under-explored save-side input-consistency nuance -- see
`build_node_states_from_save`'s docstring), the frontend calibrates the
optimizer's "optimal" estimate against the exact current figure before
showing a "gain vs. current" number, rather than subtracting two
differently-scaled figures.

## Optimizer (`app/engine/optimize.py`)

Decision variables per candidate node: merchant action (none / collect /
steer-to-`X`) and light ships (in configurable chunks). Algorithm:

1. **Seed**: home node collects (with a merchant if any are free, for the
   home bonus); nodes upstream of home steer toward it along the shortest
   path; ships placed greedily by marginal gain.
2. **Marginal completion**: remaining merchants added one at a time to
   whichever free node/option gives the best gain.
3. **Local search**: 1-opt over merchant placement/action and ship
   chunks, repeated with a few random restarts to escape local optima. A
   **repair step** removes the least-valuable merchant(s) first if a
   restart's perturbation ever exceeds the merchant budget (a real bug
   caught by a regression test: exceeding budget silently, not just
   inefficiently).
4. **Exhaustive fallback** when the candidate set is small enough
   (≤ ~200k combinations) -- also used by tests to validate the heuristic
   matches brute force on small random networks.
5. **Marginal value report**: income with one more/fewer merchant, and
   with one more/fewer chunk of light ships.

## Save parsing (`app/parsing/save.py`)

Field names are **verified against a real melted 1.37.5 save**
(`scripts/inspect_save.py` was used to dump and cross-check them), not
guessed:

- Countries present in a node are sub-blocks keyed **directly by tag**
  (`TUR={...}`, `PIR={...}`, colonial nations like `C08={...}`) --
  detected by key shape (`^[A-Z0-9]{2,4}$` + dict value), not a
  `country={tag=...}` list as an early version assumed.
- `has_trader=yes` marks a merchant present; an additional `type` key
  means it's set to Steer, absent means Collect.
- Two similarly-named but different-scale fields matter: `val` is a
  country's power-weighted share of the node's *whole* value
  (retained + forwarded); the per-country `total` field is its share of
  specifically the *retained* value. `money = total * (1 + trade_efficiency
  + merchant_present_bonus)` -- confirmed to 3-4 significant figures at
  every node where the player collects. `suggested_trade_efficiency` is
  back-solved from exactly this relationship.
- The save gives per-link steering weight only as a *node-level*
  aggregate (repeated once per outgoing link, in the same order as the
  node's edges in `data/tradenodes.json`), not per country -- used as
  relative weights to split "how much do other countries steer down each
  specific link," exact for single-link nodes, approximate for multi-link
  ones.

## Ironman melting (`app/parsing/rakaly.py`, `app/parsing/pdx_tools_melt.py`, `tools/melt_worker.py`)

Ironman saves are binary and need melting before they can be parsed as
text. This project does **not** implement or obtain Paradox's private
token dictionary itself; instead it drives
[pdx.tools](https://pdx.tools), which already melts entirely client-side
(WASM) in a browser tab, licensed to embed that dictionary.

Because the backend commonly runs in a network/process-sandboxed
environment that can't itself reach pdx.tools or launch a real browser,
the actual automation runs in a **separate process the user starts in an
ordinary terminal** (`tools/melt_worker.py`), talking to the sandboxed
backend over a plain file-based job queue (no sockets):

```
.melt_bridge/pending/<job>.eu4     -- backend writes the raw save here
.melt_bridge/processing/<job>.eu4  -- worker claims it (atomic rename)
.melt_bridge/done/<job>.melted     -- worker writes melted text here
.melt_bridge/failed/<job>.error.txt + .screenshot.png + .page.html + .console.log
                                    -- ...or full failure diagnostics
.melt_bridge/worker.heartbeat      -- refreshed every few seconds on its
                                       own thread, independent of
                                       whatever job is running, so a slow
                                       melt is never mistaken for a dead
                                       worker
```

`rakaly.py` tries this bridge first, then falls back to a local `rakaly`
CLI if one happens to be installed, then raises one clear, actionable
error naming both attempts.

Getting the actual browser automation reliable took real, confirmed bugs
found and fixed one at a time against the real save, documented in
`melt_worker.py`'s comments:

- Headless Chromium's software (SwiftShader) WebGL2 rendering trips
  pdx.tools' own "browser not supported" banner (`performanceCaveat`
  check); neutralized by monkeypatching `HTMLCanvasElement.getContext` to
  strip `failIfMajorPerformanceCaveat` before the page's own script runs,
  rather than just dismissing the banner after the fact.
- The sidebar's "Save Info" button is icon-only until a real mouse hover
  expands it; its accessible name still resolves, but Playwright's
  coordinate-based click (even `force=True`) can land on the hidden
  label's reserved space instead of the visible icon -- fixed by
  dispatching the click via the DOM (`el.click()`) instead of simulating
  a mouse click at computed coordinates.
- **The actual root cause of most of the remaining flakiness**:
  `get_by_role("button", name="Close")` substring-matches the sidebar's
  *"Close Save"* button too (which resets the whole analysis back to the
  landing page) -- once the banner stopped appearing, this "dismiss the
  banner if present" fallback was unconditionally clicking "Close Save"
  instead, silently discarding a fully successful analysis every time.
  Fixed with `exact=True`.
- Upload occasionally doesn't register at all (a React-hydration race
  right after `domcontentloaded`); since all retries were happening on
  the *same*, possibly load-broken page, the fix is `page.reload()`
  between retries, not just re-selecting the file.

## Testing

`backend/tests/` (pytest): the Clausewitz parser on hand-built snippets;
the generated graph is a DAG where every node reaches an end node; the
simulator against hand-computed exact values on toy networks (collect,
steer, passive, home bonus, non-home collect, steer-target-missing
conservation); the optimizer against exhaustive search on small random
networks; the API via FastAPI's `TestClient`; save parsing against a
hand-built fixture matching the real verified format. One test
(`test_import_save_real_ironman_end_to_end_via_live_melt_worker`) is a
genuine, best-effort end-to-end check against a real Ironman save and a
live melt worker -- it skips cleanly if no worker is running.
