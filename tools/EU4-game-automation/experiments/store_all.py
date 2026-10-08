"""Store every experiment save as a git-LFS zip (run from backend/: .venv/bin/python ../tools/EU4-game-automation/experiments/store_all.py).

Clean saves go into the dataset of their base game through the intake (app.trade.intake: zip + series.json; rejects
anything not on a 1st after the first computation, with own merchants/fleets on the way, or from another game):
  round 1 + round-2 VEN jobs (base out/E00/base_1444.12.01.eu4, experiment mod) -> exp-core-1444 (A = E00 base)
  round-2 MAM / TUR / NED jobs -> obs-1444-mam / obs-1444-tur / obs-1618-ned (A already stored)
  round-2 U10 jobs -> venice-1444 (as observation: that series has no A)
  diversity saves not yet stored (third 1st of each series) -> their obs-<year>-<tag> series (observation)
Roles: controls C (E01b C'), placement changes B<n>, everything else observation; saves made by reloading a base use
reloaded=True (EU4 draws a new seed on load). Every save the intake rejects (mid-month saves, probes, ...) is zipped
into experiments/archive/<path>.zip (LFS rule in .gitattributes). Result: experiments/STORE.json (save -> dataset id or
archive zip, with the reason)."""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.trade import intake  # noqa: E402

EXP = Path(__file__).resolve().parent
ARCHIVE = EXP / "archive"
RESULT = EXP / "STORE.json"
store = json.loads(RESULT.read_text()) if RESULT.exists() else {}


def record(path: Path, value: dict) -> None:
    store[str(path.relative_to(EXP))] = value
    RESULT.write_text(json.dumps(store, indent=1))


def archive(path: Path, reason: str) -> None:
    dst = ARCHIVE / (str(path.relative_to(EXP)) + ".zip")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(path, path.name)
    record(path, {"archive": str(dst.relative_to(EXP)), "reason": reason})


def add(path: Path, series: str, role: str, change: str, reloaded: bool) -> None:
    key = str(path.relative_to(EXP))
    if key in store:
        return
    try:
        a = intake.add_save(path, series, role, change, reloaded=reloaded)
        record(path, {"dataset": a.id, "series": series, "role": role, "zip": str(a.series_dir / (a.file + ".zip"))})
        print(f"{key}: {a.id} {series} {role}", flush=True)
    except intake.Rejected as e:
        msg = str(e)
        if role.startswith(("B", "C")) and ("must change" in msg or "must keep" in msg):
            return add(path, series, "observation", change + f" (stored as observation: {msg})", reloaded)
        archive(path, msg)
        print(f"{key}: archived ({msg[:90]})", flush=True)


SERIES_BY_BASE = {
    "E00/base_1444.12.01.eu4": "exp-core-1444",
    "obs-1444-MAM/MAM_1444.12.01.eu4": "obs-1444-mam",
    "_old_run_1/A_TUR_1444.12.01.eu4": "obs-1444-tur",
    "obs-1618-NED/NED_1618.06.01.eu4": "obs-1618-ned",
    "bases/U10_VEN.1444.12.01.eu4": "venice-1444",
}
b_counter: dict[str, int] = {}


def series_of(base: str | None) -> str | None:
    for k, v in SERIES_BY_BASE.items():
        if base and base.endswith(k):
            return v
    return None


def job_outputs(jobs_dir: Path, out_dir: Path):
    for jf in sorted(jobs_dir.glob("*.json")):
        j = json.loads(jf.read_text())
        outs = [out_dir / jf.stem / Path(s["outfname"]).name for s in j["script"] if s.get("outfname")]
        yield jf.stem, j, [o for o in outs if o.exists()]


def main() -> None:
    for jobs_dir, out_dir in ((EXP / "jobs", EXP / "out"), (EXP / "round2" / "jobs", EXP / "round2" / "out")):
        for jid, j, outs in job_outputs(jobs_dir, out_dir):
            base = j.get("base_save")
            series = series_of(base) if base else "exp-core-1444"
            kinds = [k for s in j["script"] for k in ("patch", "effects", "console_commands") if s.get(k)]
            what = ", ".join(f"{k}={Path(s[k]).name}" for s in j["script"] for k in ("patch", "effects", "console_commands") if s.get(k))
            for i, o in enumerate(outs):
                if not base:  # E00: the A save of exp-core-1444 is already stored (U30); its later 1sts are observations
                    add(o, series, "observation", f"{jid}: same session as A, no change", False)
                    continue
                control = jid in ("E01a", "E01b") or jid.endswith("-C") or "-C-" in jid
                if i > 0:
                    role = "observation"
                elif jid == "E01b":
                    role = "C'"
                elif control:
                    role = "C"
                elif "patch" in kinds:
                    b_counter[series] = b_counter.get(series, 0) + 1
                    role = f"B{b_counter[series]}"
                else:
                    role = "observation"
                add(o, series, role, f"{jid} ({what or 'no change'}), {o.name}", True)
    # diversity: saves not yet in a dataset (A and C were stored by diversity/intake_diversity.py)
    stored_div = json.loads((EXP / "diversity" / "out" / "INTAKE.json").read_text())
    taken = {v[1] for res in stored_div.values() for k, v in res.items() if k in ("A", "C")}
    for d in sorted((EXP / "diversity" / "out").glob("obs-*")):
        for o in sorted(d.glob("*.eu4")):
            if o.name not in taken:
                add(o, d.name.lower(), "observation", f"{d.name}: third 1st of the series, same session", False)
    # everything else (probes, first diversity run, round-1 mid-month saves already handled above)
    for o in sorted(EXP.glob("**/out/**/*.eu4")):
        if str(o.relative_to(EXP)) not in store and not (EXP / "diversity" / "out") in o.parents:
            archive(o, "not part of a job series (probe or retake)")
        elif (EXP / "diversity" / "out" / "_old_run_1") in o.parents and str(o.relative_to(EXP)) not in store:
            if o.name.split("_")[1] in ("CAS", "ENG", "FRA", "TUR"):
                record(o, {"dataset": "stored earlier (obs-1444-%s A/C, U33-U40)" % o.name.split("_")[1].lower()})
                continue
            archive(o, "first diversity run (AI of the nation on); its POR A had a fleet in transit")
    print(f"done: {sum(1 for v in store.values() if 'dataset' in v)} in datasets, "
          f"{sum(1 for v in store.values() if 'archive' in v)} archived", flush=True)


if __name__ == "__main__":
    main()
