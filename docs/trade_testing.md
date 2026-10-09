# Trade calculation: testing and the RED -> GREEN loop

There is exactly one calculation: `backend/app/trade/calc.py`. Tests, the verifier, the upload API, the app (`app/api.py`) and the optimizer all call it. `docs/trade_spec.md` (generated) lists its stages, every variable and every edge case. Open questions are the research tasks in `docs/research/`.

## Run it

```bash
scripts/verify_all.sh                         # full run, ~12 min (205 saves); same command as CI
EU4_FIXTURE_IDS=S14,S79 scripts/verify_all.sh  # quick subset (corpus-wide expectation tests skip)
cd backend && python3 scripts/stage_report.py  # just the dashboard
cd backend && python3 scripts/gen_spec.py      # regenerate docs/trade_spec.md after changing calc/variables/edge cases
```

CI job `verify-trade-calculation` runs `scripts/verify_all.sh`, publishes `verify-out/stage-report.md` as the job summary and as an artifact. `git lfs` must be installed for stored user cases (`git lfs pull`).

## What is checked

| Test file | What it enforces |
|---|---|
| `test_stages.py` | each stage, alone, from the save's recorded upstream values, against every fixture (all countries, all nodes); failures grouped by edge case |
| `test_chain.py` | `calc.calculate` (whole world from raw inputs only) against every recorded node value and every collector's money |
| `test_coverage.py` | every edge case is exhibited by >= 1 fixture; the uncovered list is exact and can only shrink; "must never occur" cases never occur |
| `test_variables.py` | the variable registry knows every key in every save's trade block (unknown key = a missing variable), stages/research ids are valid |
| `test_architecture.py` | only `calc.py` touches game constants; `calc.py` does no I/O; verify/tests call the same functions; no rules outside `calc.py` |
| `test_spec.py` | `docs/trade_spec.md` matches the code |
| `test_cases.py`, `test_api_verify.py`, `test_user_cases.py` | stored user cases and the upload endpoint |

## Pass means correct

A stage passes only when it reproduces the save on **every** check of **every** fixture save; the end-to-end chain passes only when `calc.calculate` reproduces every save. There is no list of accepted failures and no expected-failure marker: while any stage or any save is wrong, `scripts/verify_all.sh` and CI are red. The report (`verify-out/stage-report.md`, CI summary) shows how far off each stage is.

### Fixing a failing stage
1. Read the stage's failures (CI summary or `stage_report.py`): they are grouped by edge case with worst examples.
2. Get the rule from the matching research result (`docs/research/Rxx_*_final.md`, or the data-verified `response_<i>` while no final exists), or from the save data when it is exact.
3. Change the rule function in `calc.py` (and constants only via `game_data`; variables via `variables.py`).
4. Run `scripts/verify_all.sh` and compare the failure counts; regenerate the spec; commit.

## Datasets (the only saves tests use)

A save is used only if it is **clean** (`backend/app/trade/quality.py`; R12 final: the game computes trade once a month, on the 1st): dated the 1st after the game's first computation, with none of the player's own merchants or fleets on the way. AI traffic on the way is allowed (it is absent from both the trade entries and the computed values) and is recorded per save. `docs/research/data_audit.md` records why the 102 earlier fixture saves were removed (81 before the first computation, 21 mid-month).

```
datasets/eu4/cosmetic_mods.json                     mods that do not change game rules (they keep a save 'vanilla')
datasets/eu4/<version>/<mods key>/<dlc key>/        one dataset per game version, rule-changing mod list and DLC set
    dataset.json                                    version, mods, DLCs, protocol
    <series>/series.json + Uxx_TAG.yyyy.mm.dd.eu4.zip   one series = one game (git LFS)
    reports/                                        saves users submitted from the app (verified and logged, not gating)
```

`series.json` entries: `id, file, tag, date, role (observation | A | C | B<n> | report), change, covers (edge-case ids, e.g. ["IV-06"]), sha256, quality`. Designed experiments and how to make them: `docs/research/experiments.md`. `scripts/check_datasets.py` validates names, zips (not LFS pointers), hashes and cleanliness; `scripts/verify_all.sh` runs it first. `EU4_FIXTURE_IDS=U10,U27` / `EU4_SERIES=venice-1444` restrict a run.

Known blind spots are listed, not hidden: `KNOWN_UNCOVERED` in `expected.py` (situations no clean save exercises yet; the designed experiments close most of them).

## When a user submits a save

`POST /api/verify-save` runs the same verification and returns the save's quality. It stores nothing unless called with `store=true` (the app's "store this save for future enhancement"); then the save goes to the `reports` series of its dataset with its quality and verification summary, deduplicated by sha256. The server never commits or pushes: `git add` the new zip (LFS) and `series.json`, commit. `EU4_DATASETS_DIR` redirects the store (tests use this).
