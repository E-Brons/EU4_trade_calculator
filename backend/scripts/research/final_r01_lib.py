"""R01 final: independent loader (own code) for the whole-corpus verification of max_demand.

Per save, cached as $EU4_RESEARCH_CACHE/finalr01_<id>.pkl:
  {'id','date','kind','order': [nid...], 'nodes': {nid: {'top': tag|None, 'total': float, 'e': {tag: entry}}},
   'c': {tag: {'port': int|None, 'emb_by': [tags], 'emb_to': [tags], 'overlord': ..}}}
entry = {'md','mp','prev','val','pp','sp','tout','tin','trader','cap','coll','steer'}  (raw save keys only; no app.trade.calc)
Run from backend/ with .venv/bin/python.  Entry tags: 3 chars [A-Z0-9]; PIR (pirate stub) is skipped everywhere.
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
TOL = 0.0015   # md is stored with 3 decimals


def fl(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _entry(c: dict) -> dict:
    return {
        "md": fl(c.get("max_demand")), "mp": fl(c.get("max_pow")), "prev": fl(c.get("prev"), 0.0),
        "val": fl(c.get("val")), "pp": fl(c.get("province_power"), 0.0), "sp": fl(c.get("ship_power"), 0.0),
        "tout": fl(c.get("t_out"), 0.0), "tin": fl(c.get("t_in"), 0.0),
        "trader": bool(c.get("has_trader")), "cap": "has_capital" in c, "coll": "total" in c, "steer": "type" in c,
        "money": fl(c.get("money")), "tot": fl(c.get("total")),
    }


def load(entry: dict) -> dict:
    fp = common.CACHE / f"finalr01_{entry['id']}.pkl"
    if fp.exists():
        return pickle.loads(fp.read_bytes())
    nodes, order = {}, []
    for n in common.nodes(entry):
        nid = n["definitions"]
        order.append(nid)
        tp = as_list(n.get("top_provinces"))
        ents = {t: _entry(v) for t, v in n.items() if isinstance(v, dict) and TAGRE.match(str(t)) and t != "PIR"}
        nodes[nid] = {"top": tp[0] if tp else None, "total": fl(n.get("total"), 0.0), "e": ents}
    cs = common.block(entry, "countries")
    c = {}
    for t, v in cs.items():
        if isinstance(v, dict) and TAGRE.match(str(t)):
            c[t] = {"port": v.get("trade_port"),
                    "emb_by": [str(x) for x in as_list(v.get("trade_embargoed_by"))],
                    "emb_to": [str(x) for x in as_list(v.get("trade_embargoes"))],
                    "overlord": v.get("overlord")}
    out = {"id": entry["id"], "date": entry["date"], "kind": entry.get("kind"), "order": order, "nodes": nodes, "c": c}
    tmp = fp.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(pickle.dumps(out))
    tmp.replace(fp)
    return out


def all_saves():
    """[(id, loaded)] for all manifest entries (S01-S80, U01-U06)."""
    return [(e["id"], load(e)) for e in common.entries()]


def distinct(saves):
    """Drop U01 (copy of S80) and U02 (copy of S79)."""
    return [(i, s) for i, s in saves if i not in ("U01", "U02")]


def home_node(s: dict, tag: str):
    """Node where the country's entry has `has_capital` (the main trade port node)."""
    for nid, n in s["nodes"].items():
        e = n["e"].get(tag)
        if e and e["cap"]:
            return nid
    return None


def port_node(s: dict, tag: str):
    c = s["c"].get(tag)
    if not c or c["port"] is None:
        return None
    try:
        return PROV2NODE.get(int(c["port"]))
    except (TypeError, ValueError):
        return None


def own(e: dict) -> float:
    """Own (non-propagated) raw power of an entry = max_pow - prev (province + ship + flat extras)."""
    return (e["mp"] or 0.0) - (e["prev"] or 0.0)


def is_away(e: dict) -> bool:
    return e["coll"] and not e["cap"]
