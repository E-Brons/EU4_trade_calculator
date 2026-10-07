"""Shared loader for experiment saves: parsed top-level blocks, cached; numbers to integer thousandths."""
from __future__ import annotations
import hashlib, os, pickle, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "backend"))
from app.parsing.clausewitz import as_list, parse  # noqa: E402
from app.trade import savefile  # noqa: E402
OUT = Path(__file__).resolve().parents[1] / "out"
CACHE = Path(os.environ.get("EU4_EXP_CACHE", "/tmp/eu4exp/cache")); CACHE.mkdir(parents=True, exist_ok=True)
TAG = re.compile(r"^[A-Z0-9]{3}$")
_text = {}

def text(p: Path) -> str:
    p = Path(p)
    if p not in _text:
        _text.clear(); _text[p] = p.read_text(encoding="latin-1")
    return _text[p]

def block(p: Path, key: str):
    p = Path(p); h = hashlib.md5(f"{p.resolve()}|{p.stat().st_mtime}|{key}".encode()).hexdigest()[:16]
    f = CACHE / f"{h}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    raw = savefile.extract_top_level_block(text(p), key)
    tree = parse(raw[1:-1]) if raw else {}
    f.write_bytes(pickle.dumps(tree)); return tree

def nodes(p) -> dict:
    return {n["definitions"]: n for n in as_list(block(p, "trade").get("node")) if isinstance(n, dict) and n.get("definitions")}

def node_list(p) -> list:
    return [n for n in as_list(block(p, "trade").get("node")) if isinstance(n, dict) and n.get("definitions")]

def m3(x):
    try: return round(float(x) * 1000)
    except (TypeError, ValueError): return x

def save(eid: str, which: str) -> Path:
    d = OUT / eid
    c = sorted(d.glob(f"{which}_*.eu4"))
    return c[0] if c else None

def flat(obj, prefix=""):
    """Flatten a parsed tree into {path: scalar} (lists indexed)."""
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items(): out.update(flat(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj): out.update(flat(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out
