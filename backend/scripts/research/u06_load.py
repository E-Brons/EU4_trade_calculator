"""Loader for the Ottoman campaign series (S79, S80, U03..U06): TUR country block + trade nodes, cached."""
import pickle, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.parsing.clausewitz import as_list, parse
from app.trade import savefile, corpus

CACHE = Path("/tmp/eu4research/cache"); CACHE.mkdir(parents=True, exist_ok=True)
FIX = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "saves"
SERIES = {"S79": "S79_TUR_1665.4.22.eu4", "S80": "S80_TUR_1682.4.18.eu4", "U03": "U03_TUR.1691.01.09.eu4",
          "U04": "U04_TUR.1691.11.01.eu4", "U05": "U05_TUR.1693.04.15.eu4", "U06": "U06_TUR.1696.03.25.eu4"}

def _text(sid):
    f = FIX / SERIES[sid]
    if f.exists():
        return savefile.read_save_text(f)
    man = {e["id"]: e for e in corpus.manifest()}
    with tempfile.TemporaryDirectory() as tmp:
        return savefile.read_save_text(corpus.locate(man[sid], Path(tmp)))

def block(sid, key):
    f = CACHE / f"u06_{key}_{sid}.pkl"
    if f.exists():
        return pickle.loads(f.read_bytes())
    t = _text(sid)
    raw = savefile.extract_top_level_block(t.gamestate, key)
    tree = parse(raw[1:-1])
    f.write_bytes(pickle.dumps(tree))
    return tree

def meta_date(sid):
    t = _text(sid)
    return savefile.extract_scalar(t.meta, "date") or savefile.extract_scalar(t.gamestate, "date")

def nodes(sid):
    return [n for n in as_list(block(sid, "trade").get("node")) if isinstance(n, dict) and n.get("definitions")]

def tur(sid):
    return block(sid, "countries")["TUR"]

if __name__ == "__main__":
    for s in SERIES:
        tur(s); nodes(s); print(s, meta_date(s), flush=True)
