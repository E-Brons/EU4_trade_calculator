#!/usr/bin/env python3
"""Run every experiment job in PLAN order, unattended. Needs worker.py running in the user's iTerm tab.

    python3 tools/EU4-game-automation/experiments/run_all.py [--only E02,P01] [--skip E23]

Per job: run_job (runner.py) -> on failure one retry -> record the result in out/STATUS.json (written after every
job, so a crash loses nothing) and the log in out/<id>/run.log. Jobs whose outputs already exist and were recorded
ok are skipped, so the script can simply be restarted. Temporary runner saves (.bridge/saves/_runner_*) are deleted
after each job. E00 must succeed first (it writes the base save); if it fails, nothing else runs.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from runner import run_job  # noqa: E402

ORDER = ["E00", "E01a", "E01b", "E01c", "E01d", "P01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09",
         "E10", "E11", "E12", "E13", "E14", "E15", "E16", "E17", "E18", "E19", "E20a", "E20b", "E20c", "E20d",
         "E21", "E22", "P02", "P03", "P05", "P06", "P04", "E23"]
JOBDIR = HERE  # overridden by --dir: a folder with jobs/*.json (+ ORDER.txt), outputs in <dir>/out
STATUS = HERE / "out" / "STATUS.json"
TMP = HERE.parent / ".bridge" / "saves"
# errors that come from the machine, not the job: stop the batch instead of failing every remaining job
ENVIRONMENT_ERRORS = ("no display fits", "worker not running", "could not create image from window", "loginwindow")


def load_status() -> dict:
    return json.loads(STATUS.read_text()) if STATUS.exists() else {}


def save_status(st: dict) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1))
    tmp.rename(STATUS)


def run_one(eid: str) -> dict:
    job = JOBDIR / "jobs" / f"{eid}.json"
    logdir = JOBDIR / "out" / eid
    logdir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    def log(msg: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {msg}"
        lines.append(line)
        print(f"{eid} {line}", flush=True)
        (logdir / "run.log").write_text("\n".join(lines) + "\n")

    t0 = time.time()
    try:
        res = run_job(json.loads(job.read_text()), base=job.parent, log=log)
    except TypeError:  # run_job without base= keyword
        res = run_job(json.loads(job.read_text()), log=log)
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "error": f"{type(e).__name__}: {e}", "trace": traceback.format_exc()}
    res["seconds"] = round(time.time() - t0)
    return res


def main(argv: list[str]) -> None:
    global JOBDIR, STATUS, ORDER
    if "--dir" in argv:
        JOBDIR = Path(argv[argv.index("--dir") + 1]).resolve()
        STATUS = JOBDIR / "out" / "STATUS.json"
        order_file = JOBDIR / "ORDER.txt"
        ORDER = (order_file.read_text().split() if order_file.exists()
                 else sorted(p.stem for p in (JOBDIR / "jobs").glob("*.json")))
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    skip = set(argv[argv.index("--skip") + 1].split(",")) if "--skip" in argv else set()
    subprocess.run([sys.executable, str(HERE / "install_mod.py")], check=True)
    st = load_status()
    for eid in ORDER:
        if (only and eid not in only) or eid in skip:
            continue
        if st.get(eid, {}).get("ok"):
            print(f"{eid}: already ok, skipped", flush=True)
            continue
        res = run_one(eid)
        if any(k in (res.get("error") or "") for k in ENVIRONMENT_ERRORS):
            print(f"{eid}: environment problem ({res.get('error')}): stopping the batch; fix it and rerun "
                  "(finished jobs are skipped)", flush=True)
            break
        if not res.get("ok"):
            print(f"{eid}: failed ({res.get('error')}), retrying once", flush=True)
            first = res
            res = run_one(eid)
            res["first_attempt_error"] = first.get("error")
        st[eid] = res
        save_status(st)
        for f in TMP.glob("_runner_*.eu4"):
            f.unlink()
        print(f"{eid}: {'OK' if res.get('ok') else 'FAILED'} in {res['seconds']} s", flush=True)
        if eid == "E00" and JOBDIR == HERE and not res.get("ok"):
            print("E00 failed: no base save, stopping", flush=True)
            break
    ok = sum(1 for v in st.values() if v.get("ok"))
    print(f"done: {ok}/{len(st)} ok", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
