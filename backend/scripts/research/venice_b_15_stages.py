"""Run the current calc.py stages on the Venice saves and print per-stage failures/checks (R03 rule B, steer_weights, link_flow, income)."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.parsing.tradenodes import load_trade_graph
from app.trade.extract import extract_world
from app.trade.verify import verify_world

p = Path(sys.argv[1])
r = verify_world(extract_world(p, p.stem, graph=load_trade_graph()))
out = {k: [s.failures, s.checks] for k, s in r.stages.items() if s.status != 'not_implemented'}
worst = {k: s.worst[:2] if s.failures else [] for k, s in r.stages.items() if k in ('pull_power', 'propagation', 'raw_power', 'val', 'link_flow', 'income_efficiency')}
print(json.dumps({'save': p.stem[6:], 'calc': r.calc_version, 'stages': out, 'worst': worst}, default=str))
