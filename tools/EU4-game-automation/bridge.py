#!/usr/bin/env python3
"""Client for worker.py (file bridge). Usable from a sandboxed shell: it only writes/reads files.

    python3 tools/EU4-game-automation/bridge.py ping
    python3 tools/EU4-game-automation/bridge.py shot menu
    python3 tools/EU4-game-automation/bridge.py click 812 455
    python3 tools/EU4-game-automation/bridge.py console "helplog" "savegame spike_a"
    python3 tools/EU4-game-automation/bridge.py raw '{"verb": "key", "args": {"name": "space"}}'
"""
from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

BRIDGE = Path(__file__).resolve().parent / ".bridge"
HEARTBEAT_STALE_S = 10.0
WORKER_HINT = "start it in your own iTerm tab: python3 tools/EU4-game-automation/worker.py"


class WorkerError(RuntimeError):
    pass


def worker_alive() -> bool:
    try:
        return time.time() - float((BRIDGE / "worker.heartbeat").read_text()) < HEARTBEAT_STALE_S
    except (FileNotFoundError, ValueError):
        return False


def submit(verb: str, timeout: float = 180, **args) -> dict:
    if not worker_alive():
        raise WorkerError(f"worker not running ({WORKER_HINT})")
    job_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    pending = BRIDGE / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    tmp = pending / f"{job_id}.tmp"
    tmp.write_text(json.dumps({"verb": verb, "args": args}))
    tmp.rename(pending / f"{job_id}.json")
    done, failed = BRIDGE / "done" / f"{job_id}.json", BRIDGE / "failed" / f"{job_id}.json"
    end = time.time() + timeout
    while time.time() < end:
        for p in (done, failed):
            if p.exists():
                res = json.loads(p.read_text())
                p.unlink()
                if not res["ok"]:
                    raise WorkerError(res["error"])
                return res["result"]
        time.sleep(0.2)
    raise WorkerError(f"no answer within {timeout:.0f}s (job {job_id})")


def _num(s: str):
    try:
        return float(s) if "." in s else int(s)
    except ValueError:
        return s


def main(argv: list[str]) -> None:
    if not argv:
        print(__doc__)
        return
    verb, rest = argv[0], argv[1:]
    if verb == "raw":
        job = json.loads(rest[0])
        res = submit(job["verb"], **job.get("args", {}))
    elif verb == "console":
        res = submit("console", lines=rest)
    elif verb == "shot":
        res = submit("shot", name=rest[0] if rest else "shot")
    elif verb == "click":
        res = submit("click", x=float(rest[0]), y=float(rest[1]), **({"space": rest[2]} if len(rest) > 2 else {}))
    elif verb in ("key", "keys"):
        res = submit(verb, **({"name": rest[0]} if verb == "key" else {"text": " ".join(rest)}))
    elif verb == "launch":
        res = submit("launch", **({"args": rest} if rest else {}))
    elif verb == "wait":
        res = submit("wait", timeout=float(rest[0]) + 30, seconds=float(rest[0]))
    else:
        res = submit(verb, **{k: _num(v) for k, v in (a.split("=", 1) for a in rest)})
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except WorkerError as e:
        sys.exit(f"error: {e}")
