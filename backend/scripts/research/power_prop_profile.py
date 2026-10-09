"""Power analysis 1d: profile failing prev rows (pred>0, recorded 0) and (recorded > pred). Run from backend/."""
import sys
from collections import Counter
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data
g = game_data.graph()
prof = Counter(); over = []
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    for (node, tag), r in rec.entries.items():
        e = inp.entries[(node, tag)]
        downs = g.outgoing(node) if node in g else []
        pp = [inp.entries[(d, tag)].province_power if (d, tag) in inp.entries else 0.0 for d in downs]
        pred = calc.rule_propagated_power(pp); got = r.prev or 0.0
        if abs(pred - got) <= 0.0005:
            cls = "ok_pos" if got > 0 else "ok_zero"
        elif got == 0 and pred > 0: cls = "zero_but_pred"
        elif got > pred: cls = "over"
        else: cls = "under"
        feats = (("own_pp>0" if e.province_power > 0 else "own_pp=0"), ("trader" if e.has_trader else "-"), ("rec_maxpow>0" if (r.max_pow or 0) > 0 else "maxpow=0"))
        prof[(cls,) + feats] += 1
        if cls == "over" and len(over) < 10:
            over.append((entry["id"], inp.date, node, tag, round(pred,3), got, round(got-pred,3), e.province_power, e.ship_power, r.max_pow))
for k, v in sorted(prof.items(), key=lambda x: (x[0][0], -x[1])): print(v, k)
for o in over: print(o)
