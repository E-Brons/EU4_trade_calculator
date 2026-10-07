"""Add finished diversity series to the vanilla dataset: first save the intake accepts = A, the next = C.
Run from backend/: .venv/bin/python ../tools/EU4-game-automation/experiments/diversity/intake_diversity.py"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from app.trade import intake  # noqa: E402

HERE = Path(__file__).resolve().parent
status = json.loads((HERE / "out" / "STATUS.json").read_text())
done_file = HERE / "out" / "INTAKE.json"
done = json.loads(done_file.read_text()) if done_file.exists() else {}
for sid, st in status.items():
    if not st.get("ok") or sid in done or sid in ("obs-1444-CAS", "obs-1444-ENG", "obs-1444-FRA", "obs-1444-TUR"):
        continue
    tag = sid.split("-")[-1]; year = sid.split("-")[1]
    saves = sorted((HERE / "out" / sid).glob("*.eu4"))
    series = sid.lower(); res = {}
    desc = (f"Automated (tools/EU4-game-automation runner): new game {tag} from the {year} bookmark, spectator mode, "
            f"AI of {tag} off after the start (no own merchant/fleet moves), no mods; three 1sts saved, A = first clean one, C = next.")
    a_idx = None
    for i, s in enumerate(saves):
        try:
            r = intake.add_save(s, series, "A", "", description=desc); res["A"] = (r.id, s.name); a_idx = i; break
        except intake.Rejected as e:
            res.setdefault("rejected", []).append(f"A {s.name}: {e}")
    if a_idx is not None and a_idx + 1 < len(saves):
        try:
            r = intake.add_save(saves[a_idx + 1], series, "C", ""); res["C"] = (r.id, saves[a_idx + 1].name)
        except intake.Rejected as e:
            res.setdefault("rejected", []).append(f"C {saves[a_idx + 1].name}: {e}")
    done[sid] = res; print(sid, res, flush=True)
done_file.write_text(json.dumps(done, indent=1))
