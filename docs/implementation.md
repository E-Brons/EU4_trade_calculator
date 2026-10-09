# Implementation

## Architecture

```
frontend/ (Flutter web)  --HTTP-->  backend/ (FastAPI)
                                       |
                                       +-- app/trade/extract.py   save -> World (every country in every node)
                                       +-- app/trade/calc.py      THE trade calculation (verified against real saves)
                                       +-- app/trade/optimize.py  merchant/ship search, priced by calc.WhatIf
                                       +-- app/trade/session.py   loaded saves, kept server-side
                                       +-- app/api.py             ties it together
```

The frontend never talks to the trade model directly. It uploads a save once (`/api/import-save` returns a
`save_id`; the extracted world stays on the server) and afterwards sends only the player's decisions (merchant action
and light ships per node) plus the two player scalars it lets the user change (trade efficiency, power per added light
ship). Every number it shows comes from `calc.py`, the same code `scripts/verify_all.sh` checks against every clean
save in `datasets/` (see `docs/trade_testing.md`). The old player-centric engine (`app/engine`, `parsing/save.py`,
per-node `node_states` with `known_*` replay fields, manual data entry) was removed on 2026-10-09 (calc 0.3.0).

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

## Trade calculation (`app/trade/calc.py`)

One file holds every trade rule (one small `rule_*` function each, with the evidence in its docstring) and is the only
importer of game constants (`game_data.py`, vendored from the game by `scripts/build_game_data.py`: defines, light-ship
trade power, and the per-source values of the country modifiers `trade_steering` and `ship_power_propagation`).
`docs/trade_spec.md` (generated) lists every stage, variable and edge case. Two entry points share the rules:

- `calculate(inputs, decisions, observed)`: the whole world from raw save variables and every country's decisions.
- `predict_stage(stage, world)`: one stage from the save's recorded upstream values, so verification localises a
  mismatch to the stage that is wrong.

`WhatIf(inputs, observed, tag)` is `calculate()` for many alternative decisions of one country: everything that does
not depend on that country is computed once, each `evaluate()` takes about 2 ms instead of 10-16 ms.
`tests/trade/test_what_if.py` checks that it gives exactly what `calculate()` gives.

Values the save does not store are either derived (steering strength = `TRADE_ADDED_VALUE_MODIFER x (1 +
trade_steering)` from the country's ideas, policies, reforms, age abilities, event modifiers, navy tradition and
blockade) or identified from the save's own numbers (`identify_observed`: trade efficiency, merchant power, transfer
fraction). A variable that is truly unknown raises `UnknownVariable`; the API turns that into a 422 naming it.

## Optimizer (`app/trade/optimize.py`)

Decision variables per candidate node: merchant action (none / collect / steer-to-`X`) and light ships (sea nodes).
Every candidate placement is priced by `calc.WhatIf`:

1. **Seed**: a merchant collects at home; the others steer along the shortest path towards home; ships placed
   greedily in chunks (about 1/20 of the fleet), then single-ship moves while they help. The save's own placement is
   searched from as well, so the result is never below it.
2. **Marginal completion**: remaining merchants added one at a time where they gain most.
3. **Local search**: change one node's merchant action at a time while income rises, re-place the ships (capped at 8
   rounds), plus a few random restarts. A repair step first drops the least valuable merchants if a perturbed start
   exceeds the budget.
4. **Marginal value report**: income with one merchant / one chunk of ships more or fewer, and where.

## Save extraction (`app/trade/extract.py`, `app/trade/savefile.py`)

Reads variables only (no arithmetic): every country's entry in every node of the `trade` block (province/ship power,
flags, `max_demand`, transfers, modifiers, steering link and `add`), the node fields, the recorded results (used only
by verification), the variables of each country that select its country-scope modifiers (`countries.<TAG>`: idea
groups, policies, reforms, age abilities, modifiers, navy tradition, blockaded share; found through the save's tab
indentation so the 50+ MB document is never tokenized), and the player's merchants and light ships. Keys the variable
registry (`variables.py`) does not know are counted, and a test fails on them.

## Ironman melting (`app/parsing/ironman_melt.py`, `app/parsing/pdx_tools_browser.py`, `app/parsing/pdx_tools_melt.py`, `tools/melt_worker.py`)

Ironman saves are binary and need melting before they can be parsed as
text. This project does **not** implement or obtain Paradox's private
token dictionary itself; instead it drives
[pdx.tools](https://pdx.tools), which already melts entirely client-side
(WASM) in a browser tab, licensed to embed that dictionary.

For a normal (unsandboxed) run of this backend, the automation
(`pdx_tools_browser.melt_via_browser`) runs **directly in-process**,
dispatched to a dedicated plain thread (not the request-handling
thread, which has its own asyncio event loop that Playwright's sync API
refuses to share) -- no separate process or manual setup needed beyond
`playwright install chromium` once.

Only when that genuinely can't be attempted (no Playwright/no browser
binary in this environment -- e.g. a network/process-sandboxed dev/agent
environment that can't reach pdx.tools or launch a real browser at all)
does it fall back to a **separate process the user starts in an
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

`ironman_melt.melt_ironman_save()` tries the in-process path first, then
that bridge, then raises one clear, actionable error naming both
attempts. There is no local-CLI fallback (e.g. `rakaly`) -- pdx.tools is
the one and only melt path, in or out of process.

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

## Dashboard (`frontend/lib/screens/dashboard_screen.dart`)

One screen after import, following `docs/imported/trade-visualizations.md`.
Left: controls. Right: a Sankey of trade value flow
(`widgets/trade_sankey.dart`, geometry in `widgets/sankey_layout.dart`) over a
per-node waterfall (`widgets/node_waterfall.dart`).

- **Three presets**: *Snapshot* (the save's own allocation), *Optimal* (the
  optimizer's), *Current* (the user's last-edited allocation). Each is
  calculated through `/api/simulate` for the same loaded save, so incomes
  are directly comparable. Editing any control while Snapshot/Optimal is shown
  forks that allocation into Current; the two read-only presets never change.
- **Snapshot is the calculation of the save's own placement**: it reproduces the
  income the save records (median error 0.13 % over the 205 clean saves, see
  `docs/trade_testing.md`); the save's own figure is shown next to it
  (`actual_current_income`).
- **"Hide nodes with 0 power"** hides nodes where the active preset gives you no
  trade power. Flow to/from hidden nodes is drawn as grey stubs so totals still
  add up. To place a merchant at a node you have no power in, turn the filter off.
- Changing trade efficiency re-simulates all presets; changing the merchant/ship
  budget only marks Optimal stale until "Re-optimize" is pressed.
- Chart colours are the dataviz reference palette (blue ramp for power share,
  aqua = collect, orange = steer); aqua is below 3:1 on the light surface, so
  collect marks always carry a text label.

## Testing

`backend/tests/` (pytest): the Clausewitz parser on hand-built snippets; the generated graph is a DAG where every node
reaches an end node; the map asset; the API via FastAPI's `TestClient` on a dataset save (import, simulate, node
options, optimize); `tests/trade/` verifies `calc.py` stage by stage and end to end against every clean dataset save
(`scripts/verify_all.sh`, also the CI job), checks the variable registry, the architecture rules (one calculation, no
legacy engine), the what-if fast path and the optimizer. One test
(`test_import_save_real_ironman_end_to_end_via_live_melt_worker`) is a best-effort end-to-end check against a real
Ironman save and a live melt worker; it skips cleanly if no worker is running.
