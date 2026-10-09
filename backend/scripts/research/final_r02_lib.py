"""R02 final: independent loader (own code) for the whole-corpus verification of the away-collection penalty.

Per save (cached as $EU4_RESEARCH_CACHE/finalr02_<id>.pkl):
  {'id','date','nodes': {nid: {'top': tag|None, 'e': {tag: entry}}}, 'order': [nid...], 'c': {tag: {'port','capital','emb_by','emb_to','overlord'}}}
entry = {'md','mp','prev','val','trader','cap','coll','steer','tout','tin','keys'}
Only raw save keys are used (no app.trade.calc). Run scripts from backend/ with .venv/bin/python.
"""
from __future__ import annotations

import json
import os
import pickle
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402  (parsed-block cache only)
from app.parsing.clausewitz import as_list  # noqa: E402

GRAPH = json.loads((Path(__file__).resolve().parents[2] / "data" / "tradenodes.json").read_text())["nodes"]
PROV2NODE = {p: nid for nid, n in GRAPH.items() for p in n["member_provinces"]}
TAGRE = re.compile(r"^[A-Z0-9]{3}$")


def fl(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _entry(c: dict) -> dict:
    return {
        "md": fl(c.get("max_demand")), "mp": fl(c.get("max_pow")), "prev": fl(c.get("prev"), 0.0),
        "val": fl(c.get("val")), "tout": fl(c.get("t_out"), 0.0), "tin": fl(c.get("t_in"), 0.0),
        "trader": bool(c.get("has_trader")), "cap": "has_capital" in c, "coll": "total" in c, "steer": "type" in c,
        "keys": frozenset(c),
    }


def load(entry: dict) -> dict:
    fp = common.CACHE / f"finalr02_{entry['id']}.pkl"
    if fp.exists():
        return pickle.loads(fp.read_bytes())
    nodes, order = {}, []
    for n in common.nodes(entry):
        nid = n["definitions"]
        order.append(nid)
        tp = as_list(n.get("top_provinces"))
        ents = {t: _entry(v) for t, v in n.items() if isinstance(v, dict) and TAGRE.match(str(t))}
        nodes[nid] = {"top": tp[0] if tp else None, "e": ents}
    cs = common.block(entry, "countries")
    c = {}
    for t, v in cs.items():
        if isinstance(v, dict) and TAGRE.match(str(t)):
            c[t] = {"port": v.get("trade_port"), "capital": v.get("capital"),
                    "emb_by": [str(x) for x in as_list(v.get("trade_embargoed_by"))],
                    "emb_to": [str(x) for x in as_list(v.get("trade_embargoes"))],
                    "overlord": v.get("overlord")}
    out = {"id": entry["id"], "date": entry["date"], "nodes": nodes, "order": order, "c": c}
    tmp = fp.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(pickle.dumps(out))
    tmp.replace(fp)
    return out


def all_saves():
    """[(entry_id, loaded)] for all manifest entries."""
    return [(e["id"], load(e)) for e in common.entries()]


def port_node(s: dict, tag: str):
    """Node of the country's trade_port province, from the game's node definitions."""
    c = s["c"].get(tag)
    if not c or c["port"] is None:
        return None
    try:
        return PROV2NODE.get(int(c["port"]))
    except (TypeError, ValueError):
        return None


def capital_node(s: dict, tag: str):
    c = s["c"].get(tag)
    if not c or c["capital"] is None:
        return None
    try:
        return PROV2NODE.get(int(c["capital"]))
    except (TypeError, ValueError):
        return None


def own_power(e: dict) -> float:
    return (e["mp"] or 0.0) - (e["prev"] or 0.0)


def is_away(e: dict) -> bool:
    """Collecting (key total) without has_capital."""
    return e["coll"] and not e["cap"]


def embargo_active(s: dict, nid: str, tag: str) -> bool:
    """True iff some embargoer listed in the country's trade_embargoed_by has own power (max_pow - prev > 0) at the node."""
    c = s["c"].get(tag)
    if not c:
        return False
    ents = s["nodes"][nid]["e"]
    for emb in c["emb_by"]:
        x = ents.get(emb)
        if x and own_power(x) > 0:
            return True
    return False
