#!/usr/bin/env bash
# Start the app cleanly: kill any previous run, make sure the Flutter build is
# current, start the backend, and verify it is serving THIS build.
#
#   ./run.sh              kill old runs, (re)build if stale, serve on :8000
#   ./run.sh --no-build   skip the staleness check / rebuild
#   ./run.sh --check      only kill old runs + report, don't start anything
#   RUN_DEBUG=1 ./run.sh  trace every command (to see where it stalls)
set -u
[[ "${RUN_DEBUG:-0}" == 1 ]] && set -x

ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT=8000
BUILD="$ROOT/frontend/build/web"
BUNDLE="$BUILD/main.dart.js"

DO_BUILD=1
CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --no-build) DO_BUILD=0 ;;
    --check) CHECK_ONLY=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { printf '\033[1m==>\033[0m %s\n' "$*"; }
die() { printf '\033[31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# Run a command, but give up after $1 seconds (macOS has no `timeout`).
# A wedged process can make `lsof`/`ps` block forever; never let that stall us.
with_timeout() {
  local secs="$1"; shift
  "$@" &
  local cmd_pid=$!
  ( sleep "$secs"; kill -9 "$cmd_pid" 2>/dev/null ) >/dev/null 2>&1 &
  local watchdog=$!
  wait "$cmd_pid" 2>/dev/null
  local rc=$?
  kill "$watchdog" 2>/dev/null
  wait "$watchdog" 2>/dev/null
  return $rc
}

# True if process $1 belongs to this project, so we never kill another
# project's uvicorn / flutter run. Checked from the command line first (fast,
# can't hang): venv uvicorn and flutter's dart processes both carry this
# project's path in their arguments. Falls back to the working directory.
in_project() {
  local cmd cwd
  cmd="$(ps -o command= -p "$1" 2>/dev/null)"
  [[ "$cmd" == *"$ROOT/"* ]] && return 0
  cwd="$(with_timeout 3 lsof -a -p "$1" -d cwd -Fn 2>/dev/null | sed -n 's/^n//p')"
  [[ "$cwd" == "$ROOT" || "$cwd" == "$ROOT"/* ]]
}

kill_pid() {
  local pid="$1" why="$2"
  say "stopping $why (pid $pid)"
  kill "$pid" 2>/dev/null
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    kill -0 "$pid" 2>/dev/null || return 0
    sleep 0.3
  done
  say "pid $pid ignored SIGTERM, sending SIGKILL"
  kill -9 "$pid" 2>/dev/null
  sleep 0.3
}

# ---------------------------------------------------------------- 1. old runs
say "looking for previous runs"
found=0

# Backend: any uvicorn serving app.main from this project.
say "  checking uvicorn"
for pid in $(pgrep -f "uvicorn app.main" 2>/dev/null); do
  [[ "$pid" == "$$" ]] && continue
  if in_project "$pid"; then kill_pid "$pid" "uvicorn"; found=1; fi
done

# Frontend dev server: `flutter run` (a dart process running flutter_tools.snapshot
# with the `run` command). Deliberately NOT a loose "flutter.*run": that also
# matches dartaotruntime and other build tooling.
say "  checking flutter run"
for pid in $(pgrep -f "flutter_tools.snapshot run|bin/flutter run" 2>/dev/null); do
  [[ "$pid" == "$$" ]] && continue
  if in_project "$pid"; then kill_pid "$pid" "flutter run"; found=1; fi
done

# Whatever is still holding the port: only kill it if it belongs to this
# project; otherwise refuse, because it's someone else's server.
say "  checking port $PORT"
for pid in $(with_timeout 5 lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null); do
  if in_project "$pid"; then
    kill_pid "$pid" "process holding :$PORT"; found=1
  else
    die "port $PORT is held by pid $pid ($(ps -o command= -p "$pid" | cut -c1-100)), which is not from this project. Stop it or change PORT in run.sh."
  fi
done
[[ $found == 0 ]] && say "none running"

# ------------------------------------------------------- 2. verify they're dead
if [[ -n "$(with_timeout 5 lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null)" ]]; then
  die "port $PORT is still in use after cleanup"
fi
say "verified: port $PORT is free, no project uvicorn / flutter run alive"
[[ $CHECK_ONLY == 1 ]] && exit 0

# --------------------------------------------------------- 3. build if stale
if [[ $DO_BUILD == 1 ]]; then
  stale=0
  if [[ ! -f "$BUNDLE" ]]; then
    stale=1
  elif [[ -n "$(find "$ROOT/frontend/lib" "$ROOT/frontend/web" "$ROOT/frontend/pubspec.yaml" \
        -newer "$BUNDLE" -type f 2>/dev/null | head -1)" ]]; then
    stale=1
  fi
  if [[ $stale == 1 ]]; then
    say "frontend build is missing or older than the sources: flutter build web"
    (cd "$ROOT/frontend" && flutter build web) || die "flutter build failed"
  else
    say "frontend build is up to date"
  fi
fi
[[ -f "$BUNDLE" ]] || die "no frontend build at $BUILD (run without --no-build)"

# ------------------------------------------------------------- 4. start + verify
say "starting backend on http://localhost:$PORT"
cd "$ROOT/backend" || die "backend/ not found"
UVICORN="$ROOT/backend/.venv/bin/uvicorn"
[[ -x "$UVICORN" ]] || UVICORN="uvicorn"
"$UVICORN" app.main:app --port "$PORT" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null' EXIT INT TERM

for _ in $(seq 1 50); do
  curl -sf "http://localhost:$PORT/api/health" >/dev/null 2>&1 && break
  kill -0 "$SERVER_PID" 2>/dev/null || die "backend exited during startup"
  sleep 0.2
done
curl -sf "http://localhost:$PORT/api/health" >/dev/null 2>&1 || die "backend did not become healthy"

# The served bundle must be byte-identical to the file on disk, i.e. this
# server is really serving the build we just checked.
disk_sum="$(shasum "$BUNDLE" | cut -d' ' -f1)"
live_sum="$(curl -sf "http://localhost:$PORT/main.dart.js" | shasum | cut -d' ' -f1)"
if [[ "$disk_sum" != "$live_sum" ]]; then
  die "server on :$PORT is NOT serving $BUNDLE (sha $live_sum vs $disk_sum)"
fi
say "verified: :$PORT serves the current build ($(echo "$disk_sum" | cut -c1-8))"
build_id="$(curl -sf "http://localhost:$PORT/api/build" | sed -n 's/.*"build_id":"\([^"]*\)".*/\1/p')"
say "build id: ${build_id:-unknown}   (shown bottom-left in the app; a stale tab turns red and shows a reload banner)"
say "ready: http://localhost:$PORT/   (use a hard refresh / private window if the page looks old; Ctrl-C to stop)"

wait "$SERVER_PID"
