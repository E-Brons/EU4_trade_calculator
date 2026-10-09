"""R04 final: shared loader. Raw save keys only (no app.trade.calc). Run from backend/ with .venv/bin/python."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

COPY_OF = {"U01": "S80", "U02": "S79"}   # manifest: U01/U02 are copies of S80/S79


def m(x):
    """3-decimal fixed point as integer thousandths; asserts the value really has <= 3 decimals."""
    if x is None:
        return None
    v = round(float(x) * 1000)
    assert abs(float(x) * 1000 - v) < 1e-6, x
    return v


def is_tag(k, v):
    return isinstance(v, dict) and len(k) <= 4 and k.upper() == k


def entries_of(node):
    return {k: v for k, v in node.items() if is_tag(k, v)}


def saves():
    """Yield (id, manifest entry, nodes list) for all manifest entries."""
    for e in common.entries():
        yield e["id"], e, common.nodes(e)


def trunc_div(num, den):
    """integer division truncating toward zero (den > 0)"""
    q = abs(num) // den
    return q if num >= 0 else -q
