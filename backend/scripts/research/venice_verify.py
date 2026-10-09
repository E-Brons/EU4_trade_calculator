import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.parsing.tradenodes import load_trade_graph
from app.trade.extract import extract_world
from app.trade.verify import verify_world

p = Path(sys.argv[1])
r = verify_world(extract_world(p, p.stem, graph=load_trade_graph()))
print(json.dumps({"file": p.name, "status": r.status, "player": r.player, "date": r.date, "calc_version": r.calc_version, "first_failing_stage": r.first_failing_stage}))
