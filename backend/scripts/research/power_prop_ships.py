"""Power analysis 1e: prev with ship power in the propagated amount. Variants: ships everywhere / only in the
country's home node (has_capital), factor 0.25 (x 1/5 = 0.05). Run from backend/."""
import sys
from collections import Counter
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data
g = game_data.graph()
fx = calc.rule_fx
def prop(vals):
    return sum(fx(v / 5) for v in vals if v / 5 >= 2)
res = Counter(); left = Counter(); ex = []
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    era = "1444" if inp.date < "1450" else "later"
    for (node, tag), r in rec.entries.items():
        downs = g.outgoing(node) if node in g else []
        es = [inp.entries.get((d, tag)) for d in downs]
        got = r.prev or 0.0
        variants = {
            "base": prop(e.province_power for e in es if e),
            "ships everywhere x0.25": prop(e.province_power + 0.25 * e.ship_power for e in es if e),
            "ships at home x0.25": prop(e.province_power + (0.25 * e.ship_power if e.has_capital else 0) for e in es if e),
        }
        res[(era, "checks")] += 1
        for k, v in variants.items():
            res[(era, k)] += abs(v - got) <= 0.0005
        v = variants["ships at home x0.25"]
        if abs(v - got) > 0.0005:
            kind = "rec 0" if got == 0 else ("over" if got > v else "under")
            left[(era, kind)] += 1
            if len(ex) < 8 and kind != "rec 0": ex.append((entry["id"], inp.date, node, tag, round(v,3), got, [(d, e.province_power, e.ship_power, e.has_capital) for d, e in zip(downs, es) if e]))
for k in sorted(res): print(k, res[k])
print(left)
for x in ex: print(x)
