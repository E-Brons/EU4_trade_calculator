"""Round-2 analysis helpers: locate saves, parse blocks (cached via round-1 common), extract entries/countries."""
from __future__ import annotations
import re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
R2 = HERE.parent
EXP = R2.parent
sys.path.insert(0, str(EXP / "analysis"))
import common as c1  # noqa: E402  (round-1 loader: block(), nodes(), node_list(), m3())
from common import as_list  # noqa: E402

OUT2 = R2 / "out"
OUT1 = EXP / "out"
ENTRY_KEYS = ("val", "max_pow", "max_demand", "prev", "province_power", "ship_power", "light_ship", "has_trader", "type",
              "steer_power", "add", "t_in", "t_out", "total", "money", "has_capital", "power_fraction", "potential",
              "modifier", "t_from", "t_to")


def p2(eid, which):
    d = OUT2 / eid
    c = sorted(d.glob(f"{which}_*.eu4"))
    return c[0] if c else None


def p1(eid, which):
    d = OUT1 / eid
    c = sorted(d.glob(f"{which}_*.eu4"))
    return c[0] if c else None


def head(p):
    with open(p, "rb") as f:
        h = f.read(4096).decode("latin-1")
    g = lambda k: (m.group(1) if (m := re.search(rf'\n{k}="?([^"\n]+)"?', h)) else None)  # noqa: E731
    return {"date": g("date"), "player": g("player"), "format": h[:6]}


def entry(p, node, tag):
    n = c1.nodes(p).get(node)
    if not n:
        return None
    e = n.get(tag)
    return {k: e.get(k) for k in ENTRY_KEYS if isinstance(e, dict) and k in e} if isinstance(e, dict) else None


def node(p, nid):
    return c1.nodes(p).get(nid)


def country(p, tag):
    return c1.block(p, "countries").get(tag) or {}


def diplomacy(p):
    return c1.block(p, "diplomacy")


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
