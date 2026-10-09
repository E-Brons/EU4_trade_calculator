"""Power analysis 1b: what is the extra downstream power in failing prev values? Run from backend/."""
import sys
from collections import Counter
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data
g = game_data.graph()
n = 0; match = Counter()
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    for (node, tag), r in rec.entries.items():
        downs = g.outgoing(node) if node in g else []
        pred = calc.rule_propagated_power(inp.entries[(d, tag)].province_power if (d, tag) in inp.entries else 0.0 for d in downs)
        got = r.prev or 0.0
        if abs(pred - got) <= max(0.002, 0.05 * abs(got)): continue
        n += 1
        des = [(d, inp.entries.get((d, tag)), rec.entries.get((d, tag))) for d in downs]
        # candidate: downstream (province_power + ship_power) / 5 with threshold
        cands = {
          "pp+ship": lambda e, rr: e.province_power + e.ship_power,
          "max_pow-prev": lambda e, rr: (rr.max_pow or 0) - (rr.prev or 0),
          "max_pow": lambda e, rr: rr.max_pow or 0,
          "val": lambda e, rr: rr.val or 0,
        }
        for name, f in cands.items():
            s = sum(calc.rule_fx(f(e, rr) / 5) for d, e, rr in des if e and rr and f(e, rr) / 5 >= 2)
            if abs(s - got) <= 0.002: match[name] += 1
        if n <= 6:
            print(entry["id"], node, tag, round(pred,3), got, [(d, e.province_power, e.ship_power, rr.max_pow, rr.prev) for d, e, rr in des if e and rr])
print("fails", n, match)
