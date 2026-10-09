"""Independent helpers for the ver_*.py verification scripts (no logic shared with the authors' scripts)."""
import math, re, sys, json, pickle
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

TAG = re.compile(r'^[A-Z0-9]{2,4}$')
ENT = {e['id']: e for e in common.entries()}
PLAYED = ('S79', 'S80')
DUP = {'U01': 'S80', 'U02': 'S79'}
STARTS = [i for i in ENT if i not in PLAYED and i not in DUP]
GRAPH = json.load(open(Path(__file__).resolve().parents[2] / 'data' / 'tradenodes.json'))['nodes']


def tr3(x):
    return math.floor(x * 1000 + 1e-7) / 1000


def nodes_of(sid):
    """list of (node_id, raw_node_dict, {tag: entry_dict}) in save order"""
    out = []
    for n in common.nodes(ENT[sid]):
        ents = {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}
        out.append((n['definitions'], n, ents))
    return out


def lst(x):
    return common.as_list(x)


def fl(x, d=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d
