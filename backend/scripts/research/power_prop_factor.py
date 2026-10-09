"""Power analysis 1f: implied ship propagation factor f per (save, country): prev = sum fx((pp + f * ship)/5) over
downstream nodes (threshold 2 on the sum). Single-downstream-with-ships rows only. Run from backend/."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
from app.trade import corpus, calc, game_data
g = game_data.graph(); fx = calc.rule_fx
per = defaultdict(Counter); dist = Counter()
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    for (node, tag), r in rec.entries.items():
        downs = g.outgoing(node) if node in g else []
        es = [(d, inp.entries.get((d, tag))) for d in downs]
        es = [(d, e) for d, e in es if e and (e.province_power > 0 or e.ship_power > 0)]
        if len(es) != 1 or es[0][1].ship_power <= 0: continue
        e = es[0][1]; got = r.prev or 0.0
        if got == 0: continue
        f = round((got * 5 - e.province_power) / e.ship_power, 2)
        # snap: test candidate factors exactly
        hit = None
        for cand in (0, 0.1, 0.2, 0.25, 0.3, 0.33, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.75, 1.0):
            if abs(fx((e.province_power + cand * e.ship_power) / 5) - got) <= 0.0005: hit = cand; break
        per[(entry["id"], inp.date, tag)][hit] += 1; dist[(inp.date[:4] < "1450", hit)] += 1
print(sorted(dist.items(), key=lambda x: -x[1])[:20])
later = [(k, v) for k, v in per.items() if k[1] >= "1450"]
print(len(later)); print(later[:25])

by_era = Counter()
for (sid, date, tag), cnt in per.items():
    f = cnt.most_common(1)[0][0]
    by_era[(date[:4], f)] += 1
print(sorted(by_era.items()))
# do countries switch within a series (same tag, consecutive dates)?
