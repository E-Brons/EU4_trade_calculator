"""Step 3 overview: per treatment, VEN trade-entry fields that differ from the control (exact, thousandths),
and the treatment's country-level evidence (modifiers, techs, ideas, subjects)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import nodes, save, m3, block, as_list
CTRL = {"effects": "E01d", "patch": "E01c", "console": "E01a"}
FIELDS = ["max_pow", "max_demand", "province_power", "ship_power", "prev", "val", "money", "total", "t_out", "t_in",
          "light_ship", "add", "steer_power", "type", "has_trader", "power_fraction", "retention", "has_capital"]
NOISY = {("venice", "money"), ("venice", "total")}

def entries(eid, w, tag="VEN"):
    out = {}
    for nid, n in nodes(save(eid, w)).items():
        e = n.get(tag)
        if isinstance(e, dict):
            for f in FIELDS:
                if f in e: out[(nid, f)] = m3(e[f]) if f not in ("steer_power", "type", "has_trader", "has_capital") else e[f]
    return out

def diff(eid, ctrl, w, tag="VEN"):
    a, b = entries(ctrl, w, tag), entries(eid, w, tag)
    return {k: (a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)}

def country(eid, w, tag="VEN"):
    c = block(save(eid, w), "countries").get(tag, {})
    keys = ["technology", "active_idea_groups", "modifier", "merchants", "transfer_home_bonus", "capital", "trade_port",
            "mercantilism", "num_of_merchants", "max_historic_merchants"]
    return {k: c.get(k) for k in keys if k in c}

if __name__ == "__main__":
    kind = json.loads(sys.argv[2]) if len(sys.argv) > 2 else None
    for eid in sys.argv[1].split(","):
        job = json.load(open(Path(__file__).parents[1] / "jobs" / f"{eid}.json"))
        k = "patch" if any("patch" in s for s in job["script"]) else "effects" if any("effects" in s for s in job["script"]) else "console"
        ctrl = CTRL[k]
        print(f"===== {eid} (control {ctrl})")
        for w in ("t1", "t2"):
            d = diff(eid, ctrl, w)
            d = {kk: v for kk, v in d.items() if kk not in NOISY}
            print(f" {w}: {len(d)} VEN entry fields differ")
            for kk, v in list(d.items())[:30]: print("   ", kk, v)
