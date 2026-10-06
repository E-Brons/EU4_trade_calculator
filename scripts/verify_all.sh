#!/usr/bin/env bash
# Verifies the trade calculation (backend/app/trade/calc.py) against every fixture save. Same command locally and in CI.
#
#   scripts/verify_all.sh                      full run (about 3 minutes): stages x 80+ saves, chain, coverage, structure
#   EU4_FIXTURE_IDS=S14,S42 scripts/verify_all.sh   quick run on a few saves (corpus-wide expectation tests skip)
#   scripts/verify_all.sh -k architecture      extra arguments go to pytest
#
# Output: verify-out/stage-report.md (+ .json), the RED -> GREEN dashboard. In CI it is also the job summary.
# Exit status: 0 when every stage/chain is in the state tests/trade/expected.py says; non-zero on any drift.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend" || exit 2

PY="${PYTHON:-}"
if [[ -z "$PY" && -x .venv/bin/python ]]; then PY=.venv/bin/python; fi
PY="${PY:-python3}"

export VERIFY_OUT="${VERIFY_OUT:-$ROOT/verify-out}"
mkdir -p "$VERIFY_OUT"
rm -f "$VERIFY_OUT/stage-report.md" "$VERIFY_OUT/stage-report.json"

echo "== stored user cases: files, names, hashes"
"$PY" scripts/promote_case.py --check || exit 1

echo "== trade calculation tests"
"$PY" -m pytest tests/trade -q -rxXs -p no:cacheprovider "$@"
status=$?

if [[ -f "$VERIFY_OUT/stage-report.md" ]]; then
  echo
  sed -n '1,22p' "$VERIFY_OUT/stage-report.md"
  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then cat "$VERIFY_OUT/stage-report.md" >> "$GITHUB_STEP_SUMMARY"; fi
fi
exit $status
