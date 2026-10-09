"""Power analysis 1c: prev with a gate on the stored link weight, and the later-era residual. Run from backend/."""
import sys
from collections import Counter
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data
g = game_data.graph()
res = Counter(); later = []
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    yr = int(inp.date.split(".")[0])
    for (node, tag), r in rec.entries.items():
        downs = g.outgoing(node) if node in g else []
        w = inp.nodes[node].stored_steer_weights if node in inp.nodes else ()
        pp = [inp.entries[(d, tag)].province_power if (d, tag) in inp.entries else 0.0 for d in downs]
        base = calc.rule_propagated_power(pp)
        gated = calc.rule_propagated_power(p for i, p in enumerate(pp) if len(w) != len(downs) or w[i] > 0)
        got = r.prev or 0.0
        ok = lambda x: abs(x - got) <= 0.0005
        era = "1444" if yr < 1450 else "later"
        res[(era, "checks")] += 1
        res[(era, "base exact")] += ok(base); res[(era, "gated exact")] += ok(gated)
        if era == "later" and not ok(base) and len(later) < 12:
            later.append((entry["id"], inp.date, node, tag, round(base, 3), got, round(got - base, 3), [(d, p) for d, p in zip(downs, pp)]))
for k in sorted(res): print(k, res[k])
for x in later: print(x)
