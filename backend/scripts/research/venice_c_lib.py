"""Shared helpers for the fork-C Venice analyses: max_demand tables per (node, tag) for S01 and U07..U30."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import venice_load as V
import common
from venice_load import as_list

TAGLIKE = lambda k: isinstance(k, str) and 2 <= len(k) <= 4 and k.upper() == k


def entries_of(nodes):
    """{(node, tag): entry dict}"""
    out = {}
    for n in nodes:
        for k, v in n.items():
            if isinstance(v, dict) and TAGLIKE(k) and ("max_demand" in v or "val" in v):
                out[(n["definitions"], k)] = v
    return out


def series():
    """[(label, nodes)] : S01 then U07..U30 chronological"""
    s01 = [e for e in common.entries() if e["id"] == "S01"][0]
    res = [("S01", common.nodes(s01))]
    for i, p in enumerate(V.files()):
        res.append((f"U{7+i:02d}:{p.stem[6:]}", V.nodes(p)))
    return res
