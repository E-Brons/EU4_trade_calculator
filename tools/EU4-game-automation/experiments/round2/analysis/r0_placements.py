"""Placements (has_trader nodes with type/steer_power) and transfer_home_bonus of a tag in given saves."""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
import r2common as r
from common import nodes as _nodes


def placements(p, tag):
    out = {}
    for nid, n in _nodes(p).items():
        e = n.get(tag)
        if isinstance(e, dict) and e.get("has_trader"):
            out[nid] = ("steer" if e.get("type") == 1 else "collect", e.get("steer_power", 0) if e.get("type") == 1 else None)
    return out


if __name__ == "__main__":
    tag = sys.argv[1]
    for spec in sys.argv[2:]:
        rnd, eid, which = spec.split(":")
        p = r.p1(eid, which) if rnd == "1" else r.p2(eid, which)
        if p is None:
            print(spec, "missing"); continue
        print(spec, r.head(p)["date"], placements(p, tag), "thb", r.country(p, tag).get("transfer_home_bonus"))
