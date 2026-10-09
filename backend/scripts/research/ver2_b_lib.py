"""Second-pass verifier: independent loader (own code) for the R01/R02/R06/R07 Update 2026-10-05 checks.

Compact per-save structure, cached in $EU4_RESEARCH_CACHE as ver2b_<id>.pkl:
  {'id','date','nodes': {nid: {'top': tag|None, 'e': {tag: {...}}}}, 'order': [nid...], 'c': {tag: {...}}}
"""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402  (only used to get the parsed blocks; all logic below is new)
from app.parsing.clausewitz import as_list  # noqa: E402

GRAPH = json.loads((Path(__file__).resolve().parents[2] / "data" / "tradenodes.json").read_text())["nodes"]
PROV2NODE = {p: nid for nid, n in GRAPH.items() for p in n["member_provinces"]}


def f(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _entry(c: dict) -> dict:
    mods = [(str(m.get("key")), f(m.get("power"), 0.0)) for m in as_list(c.get("modifier")) if isinstance(m, dict)]
    return {
        "md": f(c.get("max_demand")), "mp": f(c.get("max_pow")), "prev": f(c.get("prev"), 0.0),
        "pp": f(c.get("province_power"), 0.0), "sp": f(c.get("ship_power"), 0.0), "ls": f(c.get("light_ship"), 0.0),
        "val": f(c.get("val")), "money": f(c.get("money")), "total": f(c.get("total")),
        "trader": bool(c.get("has_trader")), "cap": bool(c.get("has_capital")), "steer": "type" in c,
        "collect": "total" in c, "mods": mods, "keys": frozenset(c),
    }


def _country(c: dict) -> dict:
    gov = c.get("government") or {}
    reforms = ((gov.get("reform_stack") or {}).get("reforms") if isinstance(gov, dict) else None) or []
    est = [f(e.get("loyalty"), 0.0) for e in as_list(c.get("estate")) if isinstance(e, dict)]
    tech = c.get("technology") or {}
    return {
        "port": c.get("trade_port"), "capital": c.get("capital"),
        "emb_by": list(as_list(c.get("trade_embargoed_by"))), "ideas": dict(c.get("active_idea_groups") or {}),
        "reforms": frozenset(as_list(reforms)), "tech": (tech.get("adm_tech"), tech.get("dip_tech"), tech.get("mil_tech")),
        "merc": f(c.get("mercantilism")), "n60": sum(1 for l in est if l >= 60), "estates": tuple(est),
        "modkeys": frozenset(str(m.get("modifier")) for m in as_list(c.get("modifier")) if isinstance(m, dict)),
    }


def load(entry: dict) -> dict:
    fp = common.CACHE / f"ver2b_{entry['id']}.pkl"
    if fp.exists():
        return pickle.loads(fp.read_bytes())
    nodes, order = {}, []
    for n in common.nodes(entry):
        nid = n["definitions"]
        order.append(nid)
        tp = n.get("top_provinces")
        tp = as_list(tp)
        ents = {t: _entry(v) for t, v in n.items() if isinstance(v, dict) and t.isupper() or (isinstance(v, dict) and t[:1] in "C" and t[1:].isdigit())}
        ents = {t: e for t, e in ents.items() if t != "incoming"}
        nodes[nid] = {"top": tp[0] if tp else None, "e": ents, "total": f(n.get("total"))}
    cs = common.block(entry, "countries")
    c = {t: _country(v) for t, v in cs.items() if isinstance(v, dict) and len(t) <= 4}
    out = {"id": entry["id"], "nodes": nodes, "order": order, "c": c}
    tmp = fp.with_suffix(f".{__import__('os').getpid()}.tmp")
    tmp.write_bytes(pickle.dumps(out))
    tmp.replace(fp)
    return out


def saves(ids=None):
    for e in common.entries():
        if ids is None or e["id"] in ids:
            yield e["id"], load(e)


def home_node(s: dict, tag: str):
    """Node whose entry for `tag` carries has_capital."""
    for nid, n in s["nodes"].items():
        e = n["e"].get(tag)
        if e and e["cap"]:
            return nid
    return None


def own_power(e: dict) -> float:
    """Power an embargoer holds at the node by itself (R02 definition): max_pow - prev."""
    return (e["mp"] or 0.0) - (e["prev"] or 0.0)
