"""Shared helpers for the docs/research response analyses: cached parsed trees of the fixture saves.

Run from this backend dir with the project's .venv python. Cache dir: $EU4_RESEARCH_CACHE (default /tmp/eu4research/cache).
"""
from __future__ import annotations

import os
import pickle
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.parsing.clausewitz import as_list, parse  # noqa: E402,F401
from app.trade import corpus, savefile  # noqa: E402,F401

CACHE = Path(os.environ.get("EU4_RESEARCH_CACHE", "/tmp/eu4research/cache"))
CACHE.mkdir(parents=True, exist_ok=True)


def entries() -> list[dict]:
    return corpus.manifest()


def _text(entry: dict) -> savefile.SaveText:
    with tempfile.TemporaryDirectory() as tmp:
        return savefile.read_save_text(corpus.locate(entry, Path(tmp)))


def block(entry: dict, key: str):
    """Parsed top-level gamestate block ('trade', 'countries', 'provinces', ...), pickled in the cache. Slow the first time."""
    f = CACHE / f"{key}_{entry['id']}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    raw = savefile.extract_top_level_block(_text(entry).gamestate, key)
    tree = parse(raw[1:-1])
    tmp = f.with_suffix(f'.{os.getpid()}.tmp')
    tmp.write_bytes(pickle.dumps(tree))
    tmp.replace(f)
    return tree


def nodes(entry: dict) -> list[dict]:
    """Trade nodes in save order (`incoming.from` is 1-based into this list)."""
    return [n for n in as_list(block(entry, "trade").get("node")) if isinstance(n, dict) and n.get("definitions")]


if __name__ == "__main__":
    for e in entries():
        nodes(e)
        print(e["id"], flush=True)
