# EU4 Trade Optimizer

Tells you where to put your merchants (collect vs. steer, and to where) and
how to spread your light ships across trade nodes to maximize monthly trade
income, from your own save file.

## How it works

- **`backend/app/trade`** is the trade calculation. `extract.py` reads every
  country's entry in every trade node of a `.eu4` save (plus the country data
  that selects its trade modifiers); `calc.py` is the one file with the EU4
  trade rules, reverse-engineered from the game files and verified stage by
  stage against 205 clean real saves (`scripts/verify_all.sh`, see
  `docs/trade_testing.md` for the current status); `optimize.py` searches
  merchant/light-ship placements, each priced by `calc.WhatIf`: seed with the
  obvious choices (and the save's own placement), fill remaining merchants by
  marginal gain, then local search with random restarts.
- **`backend/app/parsing`** holds the text-format parser, the trade node graph
  (`data/tradenodes.json`, generated from the game's own
  `common/tradenodes/00_tradenodes.txt` + localisation) and the Ironman melt
  automation.
- **`backend/app/api.py`** exposes it all over HTTP; the Flutter app in
  `frontend/` is the UI.
- **Trade Atlas** (`frontend/lib/screens/atlas_view.dart`) is the default
  dashboard: a game-style world map where each trade node's land is tinted by
  a lens (your trade power / trade value / production / your income) for the
  active Snapshot / Optimal / Current preset, trade routes carry animated value
  flow, and markers show your merchants (collect / steer) and light ships. Click
  a node to fly there and open the inspector: where its value comes from, who
  holds the power, how value becomes your ducats, and live what-if cards and a
  ships-vs-income curve (`POST /api/node-options`). "Follow the money" tours the
  selected node's value downstream to its final destination. The Sankey view is
  still available via "Flow chart". Map geometry is generated from the game
  files by `backend/scripts/build_map.py` (see below).

Game constants come from the game files (`backend/data/game/`, vendored by
`backend/scripts/build_game_data.py`); values the save does not store are
derived from the country's ideas/policies/modifiers or identified from the
save's own numbers, and the two you may want to change (trade efficiency,
power per added light ship) are sliders in the UI. The income the save itself
records is shown next to the calculated Snapshot.

## Run it

### Quick start

```bash
./run.sh
```

Stops any previous uvicorn / `flutter run` from this project, verifies port
8000 is free, rebuilds the Flutter bundle if the sources are newer than
`frontend/build/web`, starts the backend, and checks that the server is
serving that exact build. Then open http://localhost:8000/. Options:
`--no-build` (skip the rebuild check), `--check` (only stop old runs and
report). Processes from other projects are never touched; if something else
holds port 8000 the script stops and says so.

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Regenerate the Atlas map geometry (`frontend/assets/map/world_map.json`, land
regions per trade node, coastlines, route curves) from a local EU4 install --
needs system `python3` with numpy and Pillow:

```bash
python3 backend/scripts/build_map.py --preview
```

Regenerate `data/tradenodes.json` from a local EU4 install (only needed if
the game patches its trade node graph):

```bash
python3 scripts/build_tradenodes.py   # auto-detects a Steam install
```

Run the tests:

```bash
pytest
```

### Frontend

```bash
cd frontend
flutter pub get
flutter run -d chrome          # dev: talks to localhost:8000
# or, for production:
flutter build web
# then just run the backend -- it serves frontend/build/web itself
```

## Save import, including Ironman

Plain-text `.eu4` saves, and saves already melted by hand (e.g. via
[pdx.tools](https://pdx.tools)'s "Melt" button), import directly with zero
extra steps.

Ironman saves are binary and need melting first. That happens
**automatically in the background** via a small file-based bridge:

1. In an ordinary, unsandboxed terminal (not through an agent's sandboxed
   tool runner -- it needs real outbound network access and to launch a
   real Chromium process):
   ```bash
   cd backend && source .venv/bin/activate
   playwright install chromium   # one-time
   python3 tools/melt_worker.py
   ```
   Leave it running while you use the app.
2. Upload an Ironman save through the app as normal. The backend drops the
   raw bytes into `backend/.melt_bridge/pending/`; the worker picks it up,
   drives a real headless Chromium tab through pdx.tools (upload -> Save
   Info -> Melt, entirely client-side WASM on their end, so the save never
   leaves your machine except to that one page), and hands the melted text
   back over the same file bridge. Typically 15-30s for a real save.

If no worker is running (or it can't reach pdx.tools), import fails with a
clear, actionable error instead of hanging, and you can always fall back to
melting by hand via pdx.tools and re-uploading the result.

See `backend/app/parsing/pdx_tools_melt.py` (the bridge client) and
`backend/tools/melt_worker.py` (the worker, plus its module docstring for
every quirk of automating pdx.tools' UI that had to be worked around) for
details.

## Documentation

- `docs/requirements.md` -- what this app is for and what it needs to do.
- `docs/implementation.md` -- how it's actually built: architecture,
  the trade calculation, the optimizer, save extraction, and the melt automation.
- `docs/trade_testing.md` -- how the calculation is verified against real
  saves; `docs/trade_spec.md` (generated) -- every stage, variable and edge
  case; `docs/research/` -- the open questions and their evidence.

## Project layout

```
backend/
  app/
    trade/      calc.py (THE trade calculation), extract.py + savefile.py
                (save -> World), optimize.py, session.py (loaded saves),
                verify.py + corpus.py (verification against datasets/),
                variables.py (variable registry), game_data.py
    parsing/    clausewitz.py (text-format parser), tradenodes.py (graph),
                ironman_melt.py + pdx_tools_browser.py + pdx_tools_melt.py
                (Ironman melt: in-process pdx.tools automation, then a
                separate worker)
    api.py, main.py, schemas.py
  data/         tradenodes.json (node graph), game/ (vendored game constants)
  scripts/      build_game_data.py, build_tradenodes.py, build_map.py,
                add_save.py, check_datasets.py, gen_spec.py, research/
  tools/        melt_worker.py (standalone Ironman-melt bridge worker)
  tests/
datasets/       clean real saves (git LFS) the calculation is verified on
frontend/       Flutter web app (import -> dashboard / atlas -> optimizer settings)
docs/           requirements.md, implementation.md, trade_testing.md, research/
```
