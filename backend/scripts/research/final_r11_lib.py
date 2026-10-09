"""R11 final: shared loader for the final_r11_*.py scripts (raw save keys only, no app.trade.calc).

Run from backend/ with .venv/bin/python. Uses the cached parsed trees of scripts/research/common.py.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

A = common.as_list
ROOT = Path(__file__).resolve().parents[2]
BASE = {k: v["trade_power"] for k, v in json.load(open(ROOT / "data/game/light_ships.json"))["ships"].items()}
GRAPH = json.load(open(ROOT / "data/tradenodes.json"))["nodes"]
INLAND = {n for n, b in GRAPH.items() if b["inland"]}
COPIES = {"U01": "S80", "U02": "S79"}   # stored user cases that are copies of S80 / S79


def fnum(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


class Save:
    def __init__(self, e):
        self.e = e
        self.id = e["id"]
        self.date = e["date"]
        self.nodes = common.nodes(e)
        self.order = [n["definitions"] for n in self.nodes]
        self.ent = {}      # (tag, node) -> entry dict
        for n in self.nodes:
            for tag, c in n.items():
                if isinstance(c, dict) and len(tag) <= 4 and tag.upper() == tag and (set(c) - {"max_demand"}):
                    self.ent[(tag, n["definitions"])] = c
        self.node_by_id = {n["definitions"]: n for n in self.nodes}
        self._cs = None

    @property
    def countries(self):
        if self._cs is None:
            self._cs = common.block(self.e, "countries")
        return self._cs

    def fleets(self):
        """All navy fleets with a protect mission: dicts with tag, node (name), light (type->count), other (type->count),
        omw ('<absent>' or value), leader, raw fleet."""
        out = []
        for tag, c in self.countries.items():
            if not isinstance(c, dict):
                continue
            for f in A(c.get("navy")):
                if not isinstance(f, dict):
                    continue
                m = f.get("mission")
                pm = m.get("protect_mission") if isinstance(m, dict) else None
                if not isinstance(pm, dict):
                    continue
                ships = [s for s in A(f.get("ship")) if isinstance(s, dict)]
                ty = Counter(s.get("type") for s in ships)
                out.append(dict(
                    tag=tag, node=self.order[int(pm["node"]) - 1], nodeidx=int(pm["node"]),
                    light={t: k for t, k in ty.items() if t in BASE},
                    other={t: k for t, k in ty.items() if t not in BASE},
                    omw=pm.get("on_my_way", "<absent>"), leader=f.get("leader"), fid=(f.get("id") or {}).get("id"),
                    name=f.get("name"), ships=ships, raw=f, pm=pm))
        return out


def saves(skip_copies=True, only_ticked=False):
    """Yield Save objects over the corpus (86 entries; copies U01/U02 skipped by default)."""
    for e in common.entries():
        if skip_copies and e["id"] in COPIES:
            continue
        yield Save(e)


def has_ships(s: Save) -> bool:
    return any("light_ship" in c or "ship_power" in c for c in s.ent.values())


import itertools


def reconcile(s: Save):
    """For every entry with light_ship: fleets at (tag,node) and the subsets whose light-ship count equals the entry.
    Returns list of dict(key, n, sp, fleets, fits=[(subset, base_sum, f)], f (None if ambiguous/no fit))."""
    fl = defaultdict(list)
    for f in s.fleets():
        fl[(f["tag"], f["node"])].append(f)
    out = []
    for key, c in s.ent.items():
        if "light_ship" not in c:
            continue
        n_e, sp = int(fnum(c["light_ship"])), fnum(c.get("ship_power"))
        fleets = fl.get(key, [])
        idx = [i for i, f in enumerate(fleets) if sum(f["light"].values()) > 0]
        fits = []
        for r in range(1, len(idx) + 1):
            for sub in itertools.combinations(idx, r):
                if sum(sum(fleets[i]["light"].values()) for i in sub) != n_e:
                    continue
                b = sum(BASE[t] * k for i in sub for t, k in fleets[i]["light"].items())
                fits.append((sub, b, sp / b))
        fs = {round(x[2], 4) for x in fits}
        out.append(dict(key=key, n=n_e, sp=sp, fleets=fleets, fits=fits, f=(fs.pop() if len(fs) == 1 else None), entry=c))
    return out


def leader_stats(cdict):
    """leader id -> leader dict (with maneuver etc.) found anywhere in the country's history."""
    out = {}

    def walk(o):
        if isinstance(o, dict):
            if "maneuver" in o and isinstance(o.get("id"), dict):
                out[o["id"]["id"]] = o
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(cdict.get("history"))
    return out
