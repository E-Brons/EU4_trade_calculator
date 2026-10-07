"""Compact per-experiment summary: for each VEN entry field, the deltas vs control and the nodes affected."""
import json, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from a4_treatments import diff, CTRL, NOISY
from common import nodes, save

def summarize(eid, w, tag="VEN"):
    job = json.load(open(Path(__file__).parents[1] / "jobs" / f"{eid}.json"))
    k = "patch" if any("patch" in s for s in job["script"]) else "effects" if any("effects" in s for s in job["script"]) else "console"
    ctrl = CTRL[k]
    d = diff(eid, ctrl, w, tag)
    allnodes = {nid for nid, n in nodes(save(ctrl, w)).items() if isinstance(n.get(tag), dict)}
    by = defaultdict(list)
    for (nid, f), (a, b) in d.items():
        if (nid, f) in NOISY and tag == "VEN": continue
        delta = (b - a) if isinstance(a, int) and isinstance(b, int) else f"{a}->{b}"
        by[f].append((nid, delta, a, b))
    out = [f"{eid} {w} vs {ctrl} ({len(allnodes)} {tag} entries):"]
    for f, rows in sorted(by.items()):
        ds = sorted({str(r[1]) for r in rows})
        nl = [r[0] for r in rows]
        if len(rows) > 8:
            out.append(f"  {f}: {len(rows)} nodes, deltas {ds[:6]}; unchanged: {sorted(allnodes - set(nl))[:12]}")
        else:
            out.append(f"  {f}: " + "; ".join(f"{r[0]} {r[2]}->{r[3]} ({r[1]})" for r in rows))
    return "\n".join(out)

if __name__ == "__main__":
    tag = sys.argv[2] if len(sys.argv) > 2 else "VEN"
    for eid in sys.argv[1].split(","):
        for w in ("t1", "t2"):
            print(summarize(eid, w, tag))
