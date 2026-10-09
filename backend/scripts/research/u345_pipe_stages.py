"""Project stage verification (verify_world) on every manifest save + the new U03/U04/U05; per-save stage summary -> JSON.
Run from backend/: .venv/bin/python scripts/research/u345_pipe_stages.py"""
import json, sys, time
from pathlib import Path
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
from app.parsing.tradenodes import load_trade_graph
from app.trade import corpus
from app.trade.extract import extract_world
from app.trade.verify import verify_world

NEW = [('U03', 'U03_TUR.1691.01.09.eu4'), ('U04', 'U04_TUR.1691.11.01.eu4'), ('U05', 'U05_TUR.1693.04.15.eu4')]
OUT = Path('/tmp/eu4research/out/pipe_stage_reports.json')
graph = load_trade_graph()
res = json.loads(OUT.read_text()) if OUT.exists() else {}

def summarize(rep):
    d = {'date': rep.date, 'player': rep.player, 'chain': {'status': rep.chain.status, 'checks': rep.chain.checks, 'failures': rep.chain.failures,
          'inc_calc': rep.chain.player_income_calculated, 'inc_rec': rep.chain.player_income_recorded,
          'worst': [(f.key, f.node, f.tag, round(f.predicted, 4), round(f.recorded, 4)) for f in rep.chain.worst[:5]]},
         'stages': {}}
    for s, r in rep.stages.items():
        d['stages'][s] = {'status': r.status, 'checks': r.checks, 'failures': r.failures, 'max_abs_error': r.max_abs_error,
                          'worst': [(f.key, f.node, f.tag, round(f.predicted, 4), round(f.recorded, 4)) for f in r.worst[:6]],
                          'by_case': r.failures_by_case}
    return d

jobs = []
for e in corpus.manifest():
    jobs.append((e['id'], corpus.FIXTURES_DIR / e['file'], e))
for sid, fn in NEW:
    jobs.append((sid, corpus.FIXTURES_DIR / fn, None))
import tempfile
for sid, path, e in jobs:
    if sid in res: continue
    t = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        p = path if path.exists() else corpus.locate(e, Path(tmp))
        w = extract_world(p, sid, graph=graph)
        res[sid] = summarize(verify_world(w))
    OUT.write_text(json.dumps(res))
    print(sid, res[sid]['date'], f'{time.time()-t:.0f}s', flush=True)
