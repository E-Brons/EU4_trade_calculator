"""VEN entry fields across the 4 controls (E01a-d) and E00: spread per field (integer thousandths)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import nodes, save, m3, block
CTRL = ["E01a", "E01b", "E01c", "E01d"]
FIELDS = ["max_pow", "max_demand", "province_power", "ship_power", "prev", "val", "money", "total", "t_out", "t_in", "light_ship", "add"]

def ven(eid, w):
    out = {}
    for nid, n in nodes(save(eid, w)).items():
        e = n.get("VEN")
        if isinstance(e, dict):
            for f in FIELDS:
                if f in e: out[(nid, f)] = m3(e[f])
    return out

if __name__ == "__main__":
    for w in ("t1", "t2"):
        data = {c: ven(c, w) for c in CTRL}
        keys = sorted(set().union(*data.values()))
        nz = 0
        for k in keys:
            vals = [data[c].get(k) for c in CTRL]
            if len(set(vals)) > 1:
                nz += 1
                if nz <= 25: print(w, k, vals)
        print(f"{w}: {nz}/{len(keys)} VEN fields vary across controls")
        cs = [block(save(c, w), "countries").get("VEN", {}) for c in CTRL]
        for f in ("treasury", "estimated_monthly_income", "transfer_home_bonus", "merchants"):
            print("  country", f, [str(c.get(f))[:40] for c in cs])
