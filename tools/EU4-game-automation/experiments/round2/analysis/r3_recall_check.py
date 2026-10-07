"""For every job whose patch calls savepatch.recall_merchant: merchant flags of the recalled entry in the base, in the
recomputed patched save (patch module applied to the base offline) and in t1. Recall jobs are void as recalls."""
import importlib.util, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r2common as r

ROOT = r.R2
JOBS = {  # job dir -> (jobs dir, out dir)
    "round1": (r.EXP / "jobs", r.OUT1), "round2": (ROOT / "jobs", r.OUT2)}


def flags(text, node, tag):
    i = text.find(f'definitions="{node}"')
    if i < 0:
        return None
    j = text.find(f"\n\t\t{tag}=", i); e = text.find("\n\t\t}", j)
    if j < 0 or j > text.find("\n\t}", i):
        return None
    b = text[j:e]
    return {"has_trader": "has_trader=yes" in b, "type": "\n\t\t\ttype=1" in b}


for rnd, (jd, od) in JOBS.items():
    for jf in sorted(jd.glob("*.json")):
        job = json.loads(jf.read_text())
        patches = [s["patch"] for s in job["script"] if s.get("patch")]
        for pm in patches:
            src = (jf.parent / pm).resolve().read_text()
            calls = re.findall(r'recall_merchant\([^,]+,\s*"(\w+)",\s*"(\w+)"\)', src)
            if not calls or not job.get("base_save"):
                continue
            base = (jf.parent / job["base_save"]).resolve()
            spec = importlib.util.spec_from_file_location("p", (jf.parent / pm).resolve())
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            bt = base.read_text(encoding="latin-1")
            try:
                pt = m.patch(bt)
            except Exception as e:  # noqa: BLE001
                print(rnd, jf.stem, "patch failed:", e); continue
            t1 = sorted((od / jf.stem).glob("t1_*.eu4"))
            tt = t1[0].read_text(encoding="latin-1") if t1 else None
            for tag, node in calls:
                print(rnd, jf.stem, tag, node, "base", flags(bt, node, tag), "patched", flags(pt, node, tag),
                      "t1", flags(tt, node, tag) if tt else "no t1", flush=True)
