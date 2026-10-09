"""Income: classify the income_efficiency failures (money at non-capital collecting nodes vs share x (1 + X + merchant)).
X per country from its capital node (calc.identify_observed). Run from backend/: .venv/bin/python scripts/research/income_failures.py"""
from collections import Counter
from app.trade import corpus, calc

stats = Counter(); fails = []
for entry, world in corpus.iter_worlds(corpus.selected()):
    obs = calc.identify_observed(world)
    inp, rec = world.inputs, world.recorded
    for (node, tag), r in rec.entries.items():
        e = inp.entries[(node, tag)]
        if r.money is None or r.share_total is None or e.has_capital or tag not in obs.trade_efficiency:
            continue
        pred = calc.rule_money(r.share_total, obs.trade_efficiency[tag], calc.rule_merchant_bonus(e.has_trader))
        stats["checks"] += 1
        ok = abs(pred - r.money) <= 0.0015
        stats["exact" if ok else "off"] += 1
        if not ok:
            ratio_x = r.money / r.share_total - 1 if r.share_total else None
            fails.append((entry["id"], entry.get("file", "")[:22], tag, node, e.has_trader, inp.nodes[node].trade_company_region,
                          round(r.share_total, 3), r.money, round(pred, 3), round(obs.trade_efficiency[tag], 3),
                          round(ratio_x, 3) if ratio_x is not None else None))
print(stats)
cls = Counter()
for f in fails:
    d = f[10] - f[9] if f[10] is not None else None
    cls[("tc" if f[5] else "notc", "merchant" if f[4] else "nomerchant", round(d, 2) if d is not None else None)] += 1
for k, v in cls.most_common(30): print(v, k)
for f in fails[:40]: print(f)
