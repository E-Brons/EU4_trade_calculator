"""Value/flow (2026-10-08): classes of the remaining steer_weights failures (calc 0.2.2).
Run from backend/: .venv/bin/python scripts/research/value_steer_failures.py [max_saves]"""
from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import calc, corpus, game_data  # noqa: E402

g = game_data.graph()
lim = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
cls = Counter(); ex = defaultdict(list); n_saves = 0
for entry, world in corpus.iter_worlds(corpus.selected()):
    n_saves += 1
    if n_saves > lim:
        break
    obs = calc.identify_observed(world)
    pairs = calc.predict_stage("steer_weights", world)
    bynode = defaultdict(list)
    for p in pairs:
        bynode[p.node].append(p)
    for node, ps in bynode.items():
        bad = any((math.isnan(p.predicted) or abs(p.predicted - p.recorded) > max(0.0011, 0.05 * abs(p.recorded))) for p in ps)
        if not bad:
            continue
        st = [(t, e) for (n, t), e in world.inputs.entries.items() if n == node and e.steering]
        rec = world.recorded
        eff = {t: (rec.entries[(node, t)].val or 0) - e.t_out + e.t_in for t, e in st}
        no_add = [t for t, e in st if e.add is None]
        unid = [t for t, e in st if t not in obs.steering_strength]
        stored = world.inputs.nodes[node].stored_steer_weights
        rw = tuple(p.recorded for p in ps)
        if not st:
            k = "no steerer (stored weights differ?)"
        elif all(eff[t] == 0 for t, _ in st):
            k = "steerers with zero effective power"
        elif unid:
            share = sum(eff[t] for t in unid) / max(sum(eff.values()), 1e-9)
            k = "unidentified strength, power share " + ("<10%" if share < 0.1 else ">=10%")
        else:
            k = "all strengths identified"
        if len(rw) and abs(sum(rw) - 1) > 0.01:
            k += ", recorded weights do not sum to 1"
        cls[k] += 1
        if len(ex[k]) < 3:
            ex[k].append((entry["id"], node, [round(p.predicted, 3) for p in ps], list(rw),
                          [(t, e.steer_link, round(eff[t], 2), e.add, round(obs.steering_strength.get(t, -1), 4)) for t, e in st][:5]))
print("saves", min(n_saves, lim), dict(cls))
for k, v in ex.items():
    print("==", k)
    for x in v:
        print("  ", x)
