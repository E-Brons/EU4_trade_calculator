"""R10 Q3: do retain_power / pull_power need a pirate term? Predict them from country entries only (project rules) and split the error by node gap."""
import sys, os, re, collections, tempfile
sys.path.insert(0, os.path.dirname(__file__))
import common
from pathlib import Path
from app.trade import corpus, calc
from app.trade.extract import extract_world
from app.parsing.tradenodes import load_trade_graph
graph = load_trade_graph()
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
c = collections.Counter(); bad = []
for e in common.entries():
    with tempfile.TemporaryDirectory() as tmp:
        w = extract_world(corpus.locate(e, Path(tmp)), e['id'], graph=graph)
    gapnodes = {}
    for n in common.nodes(e):
        if n.get('total') is None: continue
        ents = {k:v for k,v in n.items() if TAG.match(k) and isinstance(v,dict)}
        gapnodes[n['definitions']] = n['total'] - sum(v.get('val',0) for v in ents.values())
    for stage in ('retain_power','pull_power'):
        for p in calc.predict_stage(stage, w):
            has_gap = gapnodes.get(p.node, 0) > 0.0035
            ok = abs(p.predicted - p.recorded) <= 0.0035
            c[(stage, 'gap node' if has_gap else 'no-gap node', 'ok' if ok else 'FAIL')] += 1
            if not ok: bad.append((e['id'], stage, p.node, round(p.predicted,3), p.recorded, round(gapnodes.get(p.node,0),3)))
for k in sorted(c): print(k, c[k])
print(bad)
