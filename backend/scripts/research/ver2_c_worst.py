"""Second pass: worst failures per stage on the new saves and whether the raw_power error is a constant. Run from backend/."""
import sys, collections
from pathlib import Path
sys.path.insert(0, '.')
from app.parsing.tradenodes import load_trade_graph
from app.trade import calc, savefile
from app.trade.extract import extract_world
from app.trade.verify import verify_world
g = load_trade_graph()
D = Path('tests/fixtures/saves')
names = {'U03': 'U03_TUR.1691.01.09.eu4', 'U04': 'U04_TUR.1691.11.01.eu4', 'U05': 'U05_TUR.1693.04.15.eu4'}
for sid, f in names.items():
    w = extract_world(D / f, sid, graph=g)
    rep = verify_world(w, stages=('propagation', 'raw_power', 'pull_power', 'retain_power', 'steer_weights', 'income_efficiency'), with_chain=False)
    print('==', sid)
    for st in ('propagation', 'pull_power', 'retain_power', 'steer_weights', 'income_efficiency'):
        s = rep.stages[st]
        print('  ', st, f'{s.failures}/{s.checks}', [(x.node, x.tag, x.key, round(x.predicted, 3), round(x.recorded, 3)) for x in s.worst[:4]])
    diffs = collections.Counter()
    for p in calc.predict_stage('raw_power', w):
        d = round(p.predicted - p.recorded, 3)
        if abs(d) > 0.002: diffs[d] += 1
    print('   raw_power error values (predicted-recorded) among failures:', dict(diffs.most_common(6)), 'total', sum(diffs.values()))
