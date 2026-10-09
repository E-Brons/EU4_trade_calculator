"""R02 final: every row of the goal's data table (all from S79) re-derived from the save with independent code."""
import re, sys
from pathlib import Path
sys.path.insert(0, "scripts/research")
import common, final_r02_core as core

goal = Path("../docs/research/R02_away_collection_penalty_goal.md").read_text()
rows = []
for line in goal.splitlines():
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) == 11 and re.fullmatch(r"[A-Z0-9]{2,4}", cells[0]) and re.fullmatch(r"[a-z_]+", cells[1]):
        rows.append((cells[0], cells[1], float(cells[5]), float(cells[6]), float(cells[8])))
print("goal table rows:", len(rows))
e = [x for x in common.entries() if x["id"] == "S79"][0]
res, exc, d = core.per_save(e)
rws, homes, clean = d["rows"], d["homes"], d["clean"]
out = {"half": [], "embargo": [], "no_baseline": [], "other": [], "missing": []}
for tag, node, max_pow, md, ratio in rows:
    en = rws.get(tag, {}).get(node)
    if en is None:
        out["missing"].append((tag, node)); continue
    assert abs(float(en["max_demand"]) - md) < 0.0006 and abs(float(en["max_pow"]) - max_pow) < 0.0006, (tag, node, en["max_demand"], md)
    cls = core.classify(en, node, homes.get(tag))
    cl = clean(tag, node)
    others = [float(x["max_demand"]) for n2, x in rws[tag].items() if n2 != node and core.classify(x, n2, homes.get(tag)) != "away_collect" and clean(tag, n2)]
    half = [round(b, 3) for b in others if abs(md - 0.5 * b) <= core.TOL]
    if cls != "away_collect":
        out["other"].append((tag, node, cls)); continue
    if not cl:
        emb = countries_emb = d["countries"][tag].get("trade_embargoed_by")
        emb = [emb] if isinstance(emb, str) else emb
        own = {x: round(float(rws.get(x, {}).get(node, {}).get("province_power", 0) or 0) + float(rws.get(x, {}).get(node, {}).get("ship_power", 0) or 0), 1) for x in emb if x in rws and node in rws[x]}
        own = {k: v for k, v in own.items() if v > 0}
        out["embargo"].append((tag, node, md, ratio, own)); continue
    if half:
        out["half"].append((tag, node, md, half[0])); continue
    out["no_baseline" if not others else "other"].append((tag, node, md, sorted(set(round(b, 3) for b in others))[:5]))
for k, v in out.items():
    print(k, len(v))
    for x in v:
        print("   ", x)
