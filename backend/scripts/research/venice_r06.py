import sys, collections
sys.path.insert(0,'scripts/research')
import venice_load as V
from venice_load import as_list

def residuals(p):
    """residual = max_pow - province_power - ship_power - prev - 5*has_capital, per entry with max_pow; returns Counter keyed (has_trader, residual)."""
    c = collections.Counter(); ex = {}
    for n in V.nodes(p):
        for k, t in n.items():
            if isinstance(t, dict) and 'max_pow' in t:
                r = round(t['max_pow'] - t.get('province_power', 0) - t.get('ship_power', 0) - t.get('prev', 0) - 5 * bool(t.get('has_capital')), 3)
                key = (bool(t.get('has_trader')), 'mod' if 'modifier' in t else '', r)
                c[key] += 1; ex.setdefault(key, (n['definitions'], k))
    return c, ex

if __name__ == '__main__':
    for p in V.files():
        c, ex = residuals(p)
        tr = {r: v for (h, m, r), v in c.items() if h and not m}
        no = {r: v for (h, m, r), v in c.items() if not h and not m}
        print(p.stem[6:], 'merchant:', dict(sorted(tr.items())), '| no merchant:', dict(sorted(no.items())), '| with modifier:', sum(v for (h,m,r),v in c.items() if m))
