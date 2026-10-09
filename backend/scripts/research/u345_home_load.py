"""Loader for the ticked Ottoman saves S79, S80 (manifest) and U03-U05 (plain-text melted fixtures). Caches parsed blocks."""
import os, pickle, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import as_list, parse, savefile, corpus

FIX = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "saves"
NEW = {"U03": "U03_TUR.1691.01.09.eu4", "U04": "U04_TUR.1691.11.01.eu4", "U05": "U05_TUR.1693.04.15.eu4"}
IDS = ["S79", "S80", "U03", "U04", "U05"]

_text = {}
def gamestate(sid):
    if sid in _text: return _text[sid]
    if sid in NEW:
        t = savefile.read_save_text(FIX / NEW[sid]).gamestate
    else:
        e = next(x for x in common.entries() if x["id"] == sid)
        t = common._text(e).gamestate
    _text.clear(); _text[sid] = t
    return t

def block(sid, key):
    f = common.CACHE / f"{key}_{sid}.pkl"
    if f.exists(): return pickle.loads(f.read_bytes())
    raw = savefile.extract_top_level_block(gamestate(sid), key)
    tree = parse(raw[1:-1])
    tmp = f.with_suffix(f".{os.getpid()}.tmp"); tmp.write_bytes(pickle.dumps(tree)); tmp.replace(f)
    return tree

def nodes(sid):
    return [n for n in as_list(block(sid, "trade").get("node")) if isinstance(n, dict) and n.get("definitions")]

def countries(sid):
    return block(sid, "countries")

if __name__ == "__main__":
    for s in IDS:
        print(s, len(nodes(s)), len(countries(s)), flush=True)
