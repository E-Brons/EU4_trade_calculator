"""dX (money/total - 1) between consecutive saves of the campaign vs change of the country's tech levels.
Pairs are (tag, node) collecting in both saves with the same merchant status (has_trader) and the same home flag."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import u06_load as L
def f(x, d=None):
    try: return float(x)
    except (TypeError, ValueError): return d
order = ["S79","S80","U03","U04","U05","U06"]
def entries(s):
    out = {}
    for n in L.nodes(s):
        for tag, e in n.items():
            if isinstance(e, dict) and "total" in e and f(e.get("total"), 0) >= 3 and f(e.get("money")) is not None and len(tag) <= 4 and tag.isupper():
                out[(n["definitions"], tag)] = (round(f(e["money"]) / f(e["total"]) - 1, 2), bool(e.get("has_trader")), bool(e.get("has_capital")))
    return out
def techs(s):
    c = L.block(s, "countries")
    return {t: (v.get("technology") or {}) for t, v in c.items() if isinstance(v, dict)}
def main():
    tab = defaultdict(Counter)
    per_pair = {}
    for a, b in zip(order, order[1:]):
        EA, EB, TA, TB = entries(a), entries(b), techs(a), techs(b)
        pair = defaultdict(Counter)
        for k in EA:
            if k not in EB or EA[k][1:] != EB[k][1:]: continue
            tag = k[1]
            if tag not in TA or tag not in TB: continue
            da = (TB[tag].get("adm_tech", 0) - TA[tag].get("adm_tech", 0), TB[tag].get("dip_tech", 0) - TA[tag].get("dip_tech", 0), TB[tag].get("mil_tech", 0) - TA[tag].get("mil_tech", 0))
            dx = round(EB[k][0] - EA[k][0], 2)
            tab[da][dx] += 1; pair[da][dx] += 1
        print(f"-- {a}->{b}: comparable entries {sum(sum(c.values()) for c in pair.values())}")
        for da in sorted(pair): print("   d(adm,dip,mil)=", da, dict(sorted(pair[da].items(), key=lambda kv: -kv[1])[:6]))
    print("\n== pooled (adm,dip,mil) step -> dX counter (top 6)")
    for da in sorted(tab, key=lambda d: -sum(tab[d].values()))[:12]:
        print(da, sum(tab[da].values()), dict(sorted(tab[da].items(), key=lambda kv: -kv[1])[:6]))
    

if __name__ == '__main__':
    main()
