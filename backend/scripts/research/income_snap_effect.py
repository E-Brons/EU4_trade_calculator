"""Income: measured effect of the proposed calc change "identify X snapped to 0.01 inside the truncation interval of the
capital money" on the income_efficiency stage (monkeypatch of calc.identify_observed; calc.py itself is not edited).
Run from backend/: PYTHONPATH=. .venv/bin/python scripts/research/income_snap_effect.py"""
from collections import Counter
from app.trade import calc, corpus

orig = calc.identify_observed


def snapped(world):
    obs = orig(world)
    eff = dict(obs.trade_efficiency)
    for (node, tag), e in world.inputs.entries.items():
        r = world.recorded.entries.get((node, tag))
        if not (e.has_capital and r and r.money and r.share_total):
            continue
        mb = calc.rule_merchant_bonus(e.has_trader)
        lo, hi = r.money / r.share_total - 1 - mb, (r.money + 0.001) / r.share_total - 1 - mb
        cand = [v / 100 for v in range(int(lo * 100) - 1, int(hi * 100) + 2) if lo - 1e-9 <= v / 100 < hi + 1e-9]
        if len(cand) == 1:
            eff[tag] = cand[0]
    return calc.Observed(trade_efficiency=eff, merchant_power=obs.merchant_power, steering_strength=obs.steering_strength,
                         transfer_fraction=obs.transfer_fraction, default_steering_strength=obs.default_steering_strength)


def measure(fn) -> Counter:
    calc.identify_observed = fn
    c = Counter()
    for entry, world in corpus.iter_worlds(corpus.selected()):
        for p in calc.predict_stage("income_efficiency", world):
            c["checks"] += 1
            if abs(p.predicted - p.recorded) <= 0.0005: c["exact"] += 1
            elif abs(p.predicted - p.recorded) > 0.05 * max(abs(p.recorded), 1e-9): c["outside 5%"] += 1
            else: c["within 5%"] += 1
    calc.identify_observed = orig
    return c


print("current :", measure(orig))
print("snapped :", measure(snapped))
