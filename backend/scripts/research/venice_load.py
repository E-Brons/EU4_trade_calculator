"""Loader for the Venice series saves (tests/fixtures/saves/Venice*.eu4): cached parsed 'trade', 'countries' blocks.

Usage: python3 scripts/research/venice_load.py <file> ...  (fills the cache), or import load().
"""
from __future__ import annotations

import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.parsing.clausewitz import as_list, parse  # noqa: E402,F401
from app.trade import savefile  # noqa: E402

CACHE = Path(os.environ.get("EU4_RESEARCH_CACHE", "/tmp/eu4research/cache"))
SAVES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "saves"


def files() -> list[Path]:
    return sorted(SAVES.glob("Venice*.eu4"), key=lambda p: tuple(int(x) for x in p.stem[6:].split("_")))


def load(path: Path, key: str):
    f = CACHE / f"ven_{key}_{path.stem}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    text = path.read_text(encoding="utf-8", errors="replace")
    raw = savefile.extract_top_level_block(text, key)
    tree = parse(raw[1:-1])
    tmp = f.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_bytes(pickle.dumps(tree))
    tmp.replace(f)
    return tree


def nodes(path: Path) -> list[dict]:
    return [n for n in as_list(load(path, "trade").get("node")) if isinstance(n, dict) and n.get("definitions")]


if __name__ == "__main__":
    for a in sys.argv[1:]:
        p = Path(a)
        load(p, "trade")
        load(p, "countries")
        print(p.name, flush=True)
