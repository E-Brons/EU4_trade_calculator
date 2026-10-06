# Trade calculation: testing and the RED -> GREEN loop

There is exactly one calculation: `backend/app/trade/calc.py`. Tests, the verifier, the upload API and (after cutover) the optimizer all call it. `docs/trade_spec.md` (generated) lists its stages, every variable and every edge case. Open questions are the research tasks in `docs/research/`.

## Run it

```bash
scripts/verify_all.sh                         # full run, ~3 min; same command as CI
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

## When a user uploads a save that does not verify

`POST /api/verify-save` runs the same verification. On mismatch the user sees which stage failed and that results are unverified, and the save is stored as `backend/tests/fixtures/saves_zip/Uxx_TAG.yyyy.mm.dd.eu4.zip` with a manifest entry (`kind: user_case`, `expected: red`, sha256). Duplicates are not stored twice. The server never commits or pushes.

1. `git add` the new zip (LFS, see `.gitattributes`) and `backend/tests/fixtures/saves/saves.json`, commit.
2. `test_user_cases.py` fails on the case until `calc.py` reproduces it.
3. `python3 scripts/promote_case.py Uxx --green` records in the manifest that it verifies (informational). `--list` shows all cases, `--check` validates files and hashes.

Env: `EU4_STORE_CASES=0` disables storing; `EU4_CASE_ZIP_DIR` / `EU4_CASE_MANIFEST` redirect it (tests use this).

## Fixtures

`saves.json` entries: `id, file, tag, date, kind, expected, covers`. Kinds: `start` (game-start snapshot), `ticked` (played save: the only ones with ships, transfers and away collectors), `user_case`, `intervention` (change-one-thing pair from `docs/research/R14`; list the edge-case ids it exercises in `covers`, e.g. `["IV-06"]`). Raw `.eu4` files are gitignored; tracked zips in `saves_zip/` are unzipped on demand. `EU4_TEST_SAVES_DIR` points at a folder of raw saves.

Known blind spots are listed, not hidden: `KNOWN_UNCOVERED` in `expected.py` (currently no Ironman-melted save, no pirate-power node, no zero-value node, and all 16 counterfactual `IV-*` cases need intervention pairs).
