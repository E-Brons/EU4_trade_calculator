"""R09 final: loader shared by the final_r09_*.py scripts (new code; only the parser/cache of common.py is reused).

Corpus = the 86 entries of tests/fixtures/saves/saves.json (S01-S80, U01-U06). U01/U02 are copies of S80/S79, so the
'distinct' set has 84 saves. Pickles are read directly from the research cache (/tmp/eu4research/cache); a missing
pickle is produced by common.block (slow the first time, needs the zip)."""
import json, math, pickle, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import common  # noqa: E402

CACHE = common.CACHE
ENT = {e["id"]: e for e in common.entries()}
IDS = list(ENT)
DUP = {"U01": "S80", "U02": "S79"}
DISTINCT = [i for i in IDS if i not in DUP]
PLAYED = ("S79", "S80")                      # played saves (not on the 1st of a month), U01/U02 are their copies
TAG = re.compile(r"^[A-Z0-9]{2,4}$")
GRAPH = json.load(open(Path(__file__).resolve().parents[2] / "data" / "tradenodes.json"))


def tr3(x):
    """3-decimal truncation toward zero (the game's fixed point)."""
    return math.trunc(x * 1000 + (1e-7 if x >= 0 else -1e-7)) / 1000


def lst(x):
    return common.as_list(x)


def _pk(name):
    f = CACHE / name
    return pickle.loads(f.read_bytes()) if f.exists() else None


def trade(sid):
    t = _pk(f"trade_{sid}.pkl") or _pk(f"u06_trade_{sid}.pkl")
    if t is None:
        t = common.block(ENT[sid], "trade")
    return t


def nodes(sid):
    """trade nodes in save order ('incoming.from' is 1-based into this list)."""
    return [n for n in lst(trade(sid).get("node")) if isinstance(n, dict) and n.get("definitions")]


def entries_of(n):
    """{tag: entry dict} of one node (every TAG={...} block, including PIR and max_demand-only stubs)."""
    return {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}


def countries(sid):
    t = _pk(f"countries_{sid}.pkl") or _pk(f"u06_countries_{sid}.pkl")
    if t is None:
        t = common.block(ENT[sid], "countries")
    return t


def provinces(sid):
    t = _pk(f"provinces_{sid}.pkl")
    if t is None:
        t = common.block(ENT[sid], "provinces")
    return t


def fl(x, d=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


OUT = {n: [o["target"] for o in v.get("outgoing", [])] for n, v in GRAPH["nodes"].items()}
INC = {n: [] for n in OUT}
for a, bs in OUT.items():
    for b in bs:
        INC[b].append(a)
END_NODES = {n for n, v in OUT.items() if not v}


def downstream(n, _c={}):
    """all nodes reachable over >= 1 outgoing links."""
    if n not in _c:
        s = set()
        for t in OUT[n]:
            s.add(t)
            s |= downstream(t)
        _c[n] = s
    return _c[n]
