"""R06 final: independent loader (own code) for the whole-corpus verification of the flat power additions (extras).

Per save (cached as $EU4_RESEARCH_CACHE/finalr06_<id>.pkl):
  {'id','date','kind','rows': [row...], 'c': {tag: country-facts}}
row = {sid,node,tag,pp,sp,prev,mp,cap,trader,coll,steer,mods:[(key,power,power_modifier,duration)],keys}
country facts = {reforms, ideas, overlord, mods(set of modifier names), flags, policies, privs, govt}
Only raw save keys are used (no app.trade.calc). Run scripts from backend/ with .venv/bin/python.
"""
from __future__ import annotations

import os
import pickle
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402  (parsed-block cache only)
from app.parsing.clausewitz import as_list  # noqa: E402

TAGRE = re.compile(r"^[A-Z0-9]{3}$")
TOL = 0.0105  # 3-decimal storage: a sum of three stored terms can be off by a few thousandths


def fl(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def _row(sid, nid, tag, c):
    mods = []
    for m in as_list(c.get("modifier")):
        if isinstance(m, dict):
            mods.append((str(m.get("key")), fl(m.get("power"), 0.0), fl(m.get("power_modifier"), 0.0), fl(m.get("duration"))))
    return {
        "sid": sid, "node": nid, "tag": tag,
        "pp": fl(c.get("province_power"), 0.0), "sp": fl(c.get("ship_power"), 0.0), "prev": fl(c.get("prev"), 0.0),
        "mp": fl(c.get("max_pow")),
        "cap": "has_capital" in c, "trader": bool(c.get("has_trader")), "coll": "total" in c, "steer": "type" in c,
        "mods": mods, "keys": frozenset(c),
    }


def _country(c):
    gov = c.get("government") or {}
    rs = (gov.get("reform_stack") or {}) if isinstance(gov, dict) else {}
    reforms = frozenset(str(x) for x in as_list(rs.get("reforms")))
    privs = set()
    for e in as_list(c.get("estate")):
        if isinstance(e, dict):
            for gp in as_list(e.get("granted_privileges")):
                gp = as_list(gp)
                if gp:
                    privs.add(str(gp[0]))
    pol = {str(p.get("policy")) for p in as_list(c.get("active_policy")) if isinstance(p, dict)}
    mods = {str(m.get("modifier")) for m in as_list(c.get("modifier")) if isinstance(m, dict)}
    flags = frozenset(str(k) for k in (c.get("flags") or {}))
    ideas = {str(k): fl(v, 0.0) for k, v in (c.get("active_idea_groups") or {}).items()}
    return {"reforms": reforms, "ideas": ideas, "overlord": c.get("overlord"), "mods": frozenset(mods),
            "flags": flags, "policies": frozenset(pol), "privs": frozenset(privs),
            "govt": (gov.get("government") if isinstance(gov, dict) else None),
            "tg": c.get("technology_group"), "rel": c.get("religion")}


def load(entry: dict) -> dict:
    fp = common.CACHE / f"finalr06_{entry['id']}.pkl"
    if fp.exists():
        return pickle.loads(fp.read_bytes())
    rows = []
    for n in common.nodes(entry):
        nid = n["definitions"]
        for t, v in n.items():
            if isinstance(v, dict) and TAGRE.match(str(t)) and v.get("max_pow") is not None:
                rows.append(_row(entry["id"], nid, t, v))
    cs = common.block(entry, "countries")
    c = {t: _country(v) for t, v in cs.items() if isinstance(v, dict) and TAGRE.match(str(t))}
    out = {"id": entry["id"], "date": entry["date"], "kind": entry.get("kind", "start"), "rows": rows, "c": c}
    tmp = fp.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(pickle.dumps(out))
    tmp.replace(fp)
    return out


def all_saves():
    """[(entry_id, loaded)] for all manifest entries (86 entries, 84 distinct saves: U01/U02 copy S80/S79)."""
    return [(e["id"], load(e)) for e in common.entries()]


PLAYED = ("S79", "S80", "U01", "U02", "U03", "U04", "U05", "U06")
COPIES = {"U01": "S80", "U02": "S79"}


def extras(r):
    return r["mp"] - r["pp"] - r["sp"] - r["prev"]


def mod_sum(r):
    return sum(p for _, p, _, _ in r["mods"])


def residual(r):
    """extras - 5*has_capital - sum(modifier.power): what is left for the merchant term."""
    return extras(r) - 5.0 * r["cap"] - mod_sum(r)


def klass(r):
    base = "home" if r["cap"] else ("collect-away" if r["coll"] else ("steer" if r["steer"] else "passive"))
    return base + ("+merchant" if r["trader"] else "")


if __name__ == "__main__":
    for i, (sid, s) in enumerate(all_saves()):
        print(sid, len(s["rows"]), len(s["c"]), flush=True)
