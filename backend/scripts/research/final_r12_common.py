"""R12 final: shared loader for the whole-corpus checks (own code: raw parsed save keys + the trade graph only).
All stored decimals are converted to integer thousandths (m3) so identities can be tested exactly.
Run from backend/ with .venv/bin/python."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, "scripts/research")
import common

TAG = re.compile(r"^[A-Z0-9]{2,4}$")
GRAPH = json.load(open("data/tradenodes.json"))["nodes"]
OUT = {n: [o["target"] for o in v["outgoing"]] for n, v in GRAPH.items()}
END_NODES = sorted(n for n, t in OUT.items() if not t)
COPY_OF = {"U01": "S80", "U02": "S79"}          # content copies (manifest)

def lst(v):
    if v is None: return []
    return v if isinstance(v, list) else [v]

def m3(x):
    """integer thousandths of a stored number (None -> None); flags values that are not 3-decimal."""
    if x is None: return None
    y = float(x) * 1000.0
    r = round(y)
    return int(r)

def is3(x):
    y = float(x) * 1000.0
    return abs(y - round(y)) < 1e-6

def entries_of(n):
    return {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict) and (set(v) - {"max_demand"})}

def saves(distinct=False):
    """yield (id, date, kind, nodes_in_save_order) ; distinct=True skips U01/U02 (copies of S80/S79)."""
    for e in common.entries():
        if distinct and e["id"] in COPY_OF: continue
        yield e["id"], e["date"], e.get("kind", ""), common.nodes(e)

def incoming_links(nodes):
    """{(src_node, dst_node): [(value_m3, add_m3), ...]} using the 1-based `from` index of the save's node list."""
    order = [n["definitions"] for n in nodes]
    res = {}
    for n in nodes:
        for i in lst(n.get("incoming")):
            if isinstance(i, dict):
                res.setdefault((order[int(i["from"]) - 1], n["definitions"]), []).append((m3(i.get("value")) or 0, m3(i.get("add")) or 0))
    return res
