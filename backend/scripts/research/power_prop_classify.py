"""Power analysis 1: classify propagation (prev) failures over all clean saves. Run from backend/."""
import math, sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data

g = game_data.graph()
c = Counter(); by_save = Counter(); ex = []
residual_kinds = Counter()
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    pp = {k: e.province_power for k, e in inp.entries.items()}
    for (node, tag), r in rec.entries.items():
        downs = g.outgoing(node) if node in g else []
        pred = calc.rule_propagated_power(pp.get((d, tag), 0.0) for d in downs)
        got = r.prev or 0.0
        c["checks"] += 1
        if abs(pred - got) <= max(0.002, 0.05 * abs(got)):
            continue
        c["fail"] += 1; by_save[(entry["id"], inp.date)] += 1
        diff = got - pred
        # candidate explanations
        contribs = [(d, pp.get((d, tag), 0.0)) for d in downs]
        lowcontrib = sum(calc.rule_fx(p / 5) for d, p in contribs if 0 < p / 5 < 2)
        kind = "other"
        if pred == 0 and got > 0 and all((d, tag) not in inp.entries for d in downs): kind = "no downstream entry"
        elif abs(lowcontrib - diff) < 0.002: kind = "below-threshold contributions count"
        elif diff < 0: kind = "pred > recorded"
        residual_kinds[kind] += 1
        if len(ex) < 15 and kind == "other": ex.append((entry["id"], inp.date, node, tag, round(pred, 3), got, contribs))
print(dict(c)); print(residual_kinds)
print(sorted(by_save.items(), key=lambda x: -x[1])[:15])
for e in ex: print(e)
