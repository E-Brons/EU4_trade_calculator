"""Round-2 job vs control: VEN (or given tag) entries at selected nodes, country fields, and all max_demand deltas."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
import r2common as r
from common import nodes as _nodes

PAIRS = {  # job: (control round, control id, tag)
    "R2-B5a": ("1", "E01c", "VEN"), "R2-B4": ("1", "E01c", "VEN"), "R2-B5b": ("2", "R2-C-U10", "VEN"),
    "R2-B5c": ("2", "R2-C-U10", "VEN"), "R2-T05": ("1", "E01c", "MAN"), "R2-T10": ("1", "E01c", "MAN"),
    "R2-PORT": ("1", "E01c", "VEN"), "R2-CAP": ("1", "E01d", "VEN"), "R2-EMB": ("1", "E01c", "VEN"),
    "R2-STEER50": ("1", "E01d", "VEN"), "R2-STEER100": ("1", "E01d", "VEN"), "R2-IDEA1": ("1", "E01d", "VEN"),
    "R2-IDEA2": ("2", "R2-IDEA1", "VEN"), "R2-COT": ("1", "E01d", "VEN"), "R2-DEPOT": ("1", "E01d", "VEN"),
    "R2-TRIB": ("1", "E01d", "MAN"), "R2-SHIPCON": ("1", "E01c", "VEN"), "R2-PRIV": ("1", "E01c", "VEN"),
    "R2-TC": ("2", "R2-C-NED18", "NED"),
}
FIELDS = ("has_trader", "type", "steer_power", "max_demand", "max_pow", "val", "province_power", "ship_power",
          "light_ship", "t_in", "t_out", "total", "money", "has_capital", "add")


def get(rnd, eid, which):
    return r.p1(eid, which) if rnd == "1" else r.p2(eid, which)


def diff_entries(pc, pt, tag):
    nc, nt = _nodes(pc), _nodes(pt)
    out = []
    for nid in sorted(set(nc) | set(nt)):
        a = nc.get(nid, {}).get(tag); b = nt.get(nid, {}).get(tag)
        a = a if isinstance(a, dict) else {}; b = b if isinstance(b, dict) else {}
        d = {k: (a.get(k), b.get(k)) for k in FIELDS if a.get(k) != b.get(k)}
        if d:
            out.append((nid, d))
    return out


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "t1"
    jobs = sys.argv[2:] or list(PAIRS)
    for job in jobs:
        rnd, cid, tag = PAIRS[job]
        pc, pt = get(rnd, cid, which), r.p2(job, which)
        if not pc or not pt:
            print(job, "missing", pc, pt); continue
        cc, ct = r.country(pc, tag), r.country(pt, tag)
        cdiff = {k: (cc.get(k), ct.get(k)) for k in ("transfer_home_bonus", "trade_port", "capital", "trade_embargoes",
                                                    "trade_embargoed_by", "mercantilism", "active_idea_groups", "merchants")
                 if cc.get(k) != ct.get(k) and k != "merchants"}
        print(f"== {job} vs {cid} [{which}] tag {tag}: {r.head(pt)['date']} player {r.head(pt)['player']} | country {cdiff}")
        for nid, d in diff_entries(pc, pt, tag)[:14]:
            print("   ", nid, d)
