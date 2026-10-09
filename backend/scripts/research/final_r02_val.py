"""R02 final, test 6: the penalty sits in max_demand, so it hits every component of max_pow: val == max_pow * max_demand for
the away-collecting entries, and the away entries cover ship power, propagated power (prev), merchant-only entries.
Usage: .venv/bin/python scripts/research/final_r02_val.py"""
import sys
from collections import Counter
sys.path.insert(0, "scripts/research")
import common
import final_r02_lib as L

c = Counter()
worst = (0, None)
bad = []
for e in common.entries():
    for n in common.nodes(e):
        for tag, v in n.items():
            if not (isinstance(v, dict) and L.TAGRE.match(str(tag)) and "total" in v and "has_capital" not in v):
                continue
            c["away entries"] += 1
            val, mp, md = L.fl(v.get("val")), L.fl(v.get("max_pow")), L.fl(v.get("max_demand"))
            ship, prev, prov = L.fl(v.get("ship_power"), 0.0), L.fl(v.get("prev"), 0.0), L.fl(v.get("province_power"), 0.0)
            if ship > 0: c["  with ship_power > 0"] += 1
            if prev > 0: c["  with prev > 0"] += 1
            if prov == 0: c["  with province_power == 0 (merchant / flat only)"] += 1
            if "t_out" in v: c["  with t_out (power given to an overlord)"] += 1
            if val is None or mp is None or md is None:
                c["  val/max_pow/max_demand missing"] += 1
                continue
            dev = abs(val - mp * md)
            tol = 0.0005 * mp + 0.0006   # md is rounded to 3 decimals, val is truncated
            if dev <= tol:
                c["  val == max_pow * max_demand within rounding"] += 1
            else:
                bad.append((e["id"], n["definitions"], tag, val, mp, md, round(mp * md, 3)))
print(dict(c))
print("exceptions:", bad)

# transfers: a subject's t_out is computed from its (already halved) val: t_out = 0.5 * (val - 0.1) in the R04 stage
cc = Counter(); off = []
for e in common.entries():
    for n in common.nodes(e):
        for tag, v in n.items():
            if isinstance(v, dict) and L.TAGRE.match(str(tag)) and "total" in v and "has_capital" not in v and "t_out" in v:
                val, to = L.fl(v.get("val")), L.fl(v.get("t_out"))
                cc["away entries with t_out"] += 1
                if abs(to - 0.5 * (val - 0.1)) <= 0.0015:
                    cc["t_out == 0.5*(val-0.1) within 0.0015"] += 1
                else:
                    off.append((e["id"], n["definitions"], tag, val, to, round(0.5 * (val - 0.1), 3)))
print(dict(cc), "exceptions:", off)
