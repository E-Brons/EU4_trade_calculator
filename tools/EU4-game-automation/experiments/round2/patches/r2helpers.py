"""Round-2 save edits not covered by savepatch.py. Formats are copied from saves:
- transfer relation (U25 diplomacy block): transfer_trade_power={ amount=1.000 is_enforced=yes first="LDU" second="MRA" start_date=... }
  (U04: 24 colony / trade protectorate relations, all amount=0.500)
- embargo (U25 country blocks): embargoer `trade_embargoes={ TAG }`, target `trade_embargoed_by={ TAG }`, both just
  before `score_rating=` in the country block
- main trade port: country field `trade_port=<province id>` (E00: VEN capital=112, trade_port=112)
"""
import re


def country_span(t: str, tag: str) -> tuple[int, int]:
    c = t.index("\ncountries={")
    i = t.index(f"\n\t{tag}={{", c)
    return i, t.index("\n\t}", i)


def add_transfer(t: str, giver: str, receiver: str, amount: float, date: str) -> str:
    d = t.index("\ndiplomacy={")
    rel = (f"\n\ttransfer_trade_power={{\n\t\tamount={amount:.3f}\n\t\tis_enforced=yes\n\t\tfirst=\"{giver}\""
           f"\n\t\tsecond=\"{receiver}\"\n\t\tstart_date={date}\n\t}}")
    k = d + len("\ndiplomacy={")
    return t[:k] + rel + t[k:]


def _add_list(t: str, tag: str, key: str, item: str) -> str:
    i, e = country_span(t, tag)
    blk = t[i:e]
    m = re.search(rf"\n\t\t{key}={{([^}}]*)}}", blk)
    if m:
        if item in m.group(1).split():
            return t
        new = blk[:m.start(1)] + m.group(1).rstrip() + f" {item} \n\t\t" + blk[m.end(1):]
    else:
        j = blk.index("\n\t\tscore_rating=")
        new = blk[:j] + f"\n\t\t{key}={{\n\t\t\t{item} \n\t\t}}" + blk[j:]
    return t[:i] + new + t[e:]


def add_embargo(t: str, embargoer: str, target: str) -> str:
    t = _add_list(t, embargoer, "trade_embargoes", target)
    return _add_list(t, target, "trade_embargoed_by", embargoer)


def set_trade_port(t: str, tag: str, province: int) -> str:
    i, e = country_span(t, tag)
    blk = t[i:e]
    new, n = re.subn(r"\n\t\ttrade_port=\d+", f"\n\t\ttrade_port={province}", blk, count=1)
    assert n == 1, "trade_port field not found"
    return t[:i] + new + t[e:]


def privateer(t: str, tag: str, node: str) -> str:
    """Experimental: protect-trade mission in `node` (savepatch), then the mission key renamed to privateer_mission
    (key present in the game binary; field set of a real privateer mission not seen in any save)."""
    import savepatch as sp
    t2 = sp.set_light_ship_mission(t, tag, node)
    i, e = country_span(t2, tag)
    blk = t2[i:e]
    j = blk.rfind("protect_mission={")
    assert j >= 0
    return t2[:i] + blk[:j] + "privateer_mission={" + blk[j + len("protect_mission={"):] + t2[e:]
