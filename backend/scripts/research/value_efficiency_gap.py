"""Value/flow (2026-10-08): why does the chain stop on unknown trade_efficiency? Classify the countries that collect in
the chain but get no identified efficiency (identify_observed uses only the capital node), and test a fallback:
efficiency from any collecting entry with recorded money and share (money/share - 1 - merchant bonus), the most common
value per country. Run from backend/: .venv/bin/python scripts/research/value_efficiency_gap.py"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import calc, corpus  # noqa: E402

c = Counter(); fallback_ok = Counter()
for entry, world in (corpus.iter_worlds(corpus.selected()) if __name__ == "__main__" and "--proposed" not in sys.argv else []):
    obs = calc.identify_observed(world)
    rec = world.recorded
    for (node, tag), e in world.inputs.entries.items():
        if not e.collecting or tag in obs.trade_efficiency:
            continue
        r = rec.entries.get((node, tag))
        kind = ("capital entry" if e.has_capital else "away") + (", money" if r and r.money else ", no money") + (", share" if r and r.share_total else ", no share")
        c[kind] += 1
    # fallback
    vals = defaultdict(Counter)
    for (node, tag), e in world.inputs.entries.items():
        r = rec.entries.get((node, tag))
        if e.collecting and r and r.money and r.share_total and tag not in obs.trade_efficiency:
            vals[tag][round(calc.rule_trade_efficiency(r.money, r.share_total, calc.rule_merchant_bonus(e.has_trader)), 2)] += 1
    eff = dict(obs.trade_efficiency); eff.update({t: v.most_common(1)[0][0] for t, v in vals.items()})
    obs2 = replace(obs, trade_efficiency=eff)
    try:
        calc.calculate(world.inputs, world.inputs.decisions, obs2); fallback_ok["chain completes"] += 1
    except calc.UnknownVariable as ex:
        fallback_ok["still unknown: " + str(ex)[:60]] += 1
if __name__ == "__main__": print("collecting entries without identified efficiency:", dict(c))
if __name__ == "__main__": print("with the fallback:", dict(fallback_ok))


def proposed_observed(world):
    """Proposed: efficiency 0.0 (irrelevant) for countries whose collecting entries all have no power, plus the
    fallback from any collecting entry with recorded money (most common value)."""
    obs = calc.identify_observed(world)
    rec = world.recorded
    eff = dict(obs.trade_efficiency)
    vals = defaultdict(Counter)
    for (node, tag), e in world.inputs.entries.items():
        r = rec.entries.get((node, tag))
        if e.collecting and r and r.money and r.share_total and tag not in eff:
            vals[tag][round(calc.rule_trade_efficiency(r.money, r.share_total, calc.rule_merchant_bonus(e.has_trader)), 2)] += 1
    eff.update({t: v.most_common(1)[0][0] for t, v in vals.items()})
    for (node, tag), e in world.inputs.entries.items():
        r = rec.entries.get((node, tag))
        if (e.has_capital or e.collecting) and tag not in eff and not (r and r.money):
            eff[tag] = 0.0   # no recorded money anywhere (no power, or a share that truncates to 0): not identifiable
    return replace(obs, trade_efficiency=eff)


if __name__ == "__main__" and "--proposed" in sys.argv:
    from app.trade import verify
    st = Counter(); inc = []
    for entry, world in corpus.iter_worlds(corpus.selected()):
        obs = proposed_observed(world)
        try:
            res = calc.calculate(world.inputs, world.inputs.decisions, obs)
        except calc.UnknownVariable as ex:
            st["unknown " + str(ex)[:50]] += 1; continue
        cur = [(n, res.nodes[n].current, nr.current) for n, nr in world.recorded.nodes.items() if nr.current is not None and n in res.nodes]
        bad = sum(1 for _n, p, r in cur if not verify.close(p, r, *verify.CHAIN_TOLERANCE))
        st["chain completes"] += 1; st["nodes current off (chain tol)"] += bad; st["nodes checked"] += len(cur)
        rec_inc = sum(r.money or 0 for (n, t), r in world.recorded.entries.items() if t == world.inputs.player)
        inc.append((entry["id"], round(res.income(world.inputs.player), 3), round(rec_inc, 3)))
    print(dict(st))
    ok = sum(1 for _i, p, r in inc if verify.close(p, r, *verify.CHAIN_TOLERANCE)); print("player income within chain tolerance:", ok, "of", len(inc))
    print(sorted(inc, key=lambda x: -abs(x[1] - x[2]) / max(x[2], 1e-9))[:8])
