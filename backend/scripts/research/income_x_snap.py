"""Income: is the residual error of `money` only the imprecise identification of X at the capital?
X_cap = money/share - 1 - merchant at the capital has truncation error ~0.001/share (large for small shares).
Variants: raw X; X from the capital entry with the largest share (same); X snapped to 0.01 / 0.05; X as the median
over all the country's collecting entries (each corrected for its merchant). Run from backend/ with PYTHONPATH=."""
import statistics
from collections import Counter, defaultdict
from app.trade import corpus, calc

def money_pred(share, x, merchant):
    return calc.rule_money(share, x, calc.rule_merchant_bonus(merchant))

res = Counter(); away_extra = Counter(); ex = []
for entry, world in corpus.iter_worlds(corpus.selected()):
    inp, rec = world.inputs, world.recorded
    rows = defaultdict(list)
    for (node, tag), r in rec.entries.items():
        e = inp.entries[(node, tag)]
        if r.money and r.share_total and r.share_total > 0:
            rows[tag].append((node, e, r))
    for tag, lst in rows.items():
        cap = [x for x in lst if x[1].has_capital]
        if not cap:
            continue
        node0, e0, r0 = cap[0]
        x_raw = calc.rule_trade_efficiency(r0.money, r0.share_total, calc.rule_merchant_bonus(e0.has_trader))
        # interval of X consistent with the truncated capital money: money in [m, m+0.001)
        lo = (r0.money) / r0.share_total - 1 - calc.rule_merchant_bonus(e0.has_trader)
        hi = (r0.money + 0.001) / r0.share_total - 1 - calc.rule_merchant_bonus(e0.has_trader)
        cands = {"raw": x_raw, "snap01": round(x_raw, 2), "snap005": round(x_raw * 20) / 20,
                 "snap01_in_interval": next((v / 100 for v in range(int(lo * 100) - 1, int(hi * 100) + 2) if lo - 1e-9 <= v / 100 < hi + 1e-9), round(x_raw, 2))}
        for node, e, r in lst:
            if e.has_capital:
                continue
            for k, x in cands.items():
                ok = abs(money_pred(r.share_total, x, e.has_trader) - r.money) <= 0.0005
                res[(k, ok)] += 1
            x = cands["snap01_in_interval"]
            if abs(money_pred(r.share_total, x, e.has_trader) - r.money) > 0.0005:
                implied = r.money / r.share_total - 1 - calc.rule_merchant_bonus(e.has_trader) - x
                away_extra[(round(implied, 2), e.has_trader, inp.nodes[node].trade_company_region)] += 1
                if len(ex) < 25: ex.append((entry["id"], tag, node, e.has_trader, inp.nodes[node].trade_company_region, r.share_total, r.money, round(implied, 3)))
for k in ("raw", "snap01", "snap005", "snap01_in_interval"):
    print(f"{k:20s} exact {res[(k, True)]:5d}  off {res[(k, False)]:4d}")
print("residual X at failing away entries (implied extra, has_trader, tc region):")
for k, v in away_extra.most_common(15): print(" ", v, k)
for x in ex: print(" ", x)
