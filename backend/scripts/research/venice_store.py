"""Store the Venice series saves as user cases U07.. (zip + saves.json entry), in chronological order."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import venice_load as V
from app.parsing.tradenodes import load_trade_graph
from app.trade import cases
from app.trade.extract import extract_world
from app.trade.savefile import read_save_text
from app.trade.verify import verify_world

graph = load_trade_graph()
for p in V.files():
    text = read_save_text(p)
    report = verify_world(extract_world(p, p.stem, graph=graph))
    s = cases.store_case(text, report)
    print(p.name, "->", s.id, s.file, "duplicate" if s.duplicate else "stored", flush=True)
