"""R04 Q4: prev of entries whose downstream entry is a receiver (t_in>0) / giver (t_out>0): does the plain province_power rule still hold? Also receivers' max_pow decomposition."""
import sys, json, collections
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import as_list
G = json.load(open(Path(__file__).resolve().parents[2] / 'data' / 'tradenodes.json'))['nodes']
out = {n: [o['target'] for o in v['outgoing']] for n, v in G.items()}
def d5(p): return float((D(repr(float(p))) / 5).quantize(D('0.001'), rounding=ROUND_DOWN))
def tags(n): return {t: c for t, c in n.items() if isinstance(c, dict) and t.upper() == t and len(t) <= 4}
PLAYED = {'S79', 'S80', 'U01', 'U02'}
res = collections.Counter(); mp = collections.Counter()
for e in common.entries():
    sid = e['id']; snap = sid not in PLAYED
    ns = {n['definitions']: n for n in common.nodes(e)}; T = {k: tags(n) for k, n in ns.items()}
    for B, tg in T.items():
        sp = as_list(ns[B].get('steer_power'))
        for tag in set(tg) | {t for D_ in out.get(B, []) for t in T.get(D_, {})}:
            links = [(sp[i] if i < len(sp) else 0, T[D_][tag]) for i, D_ in enumerate(out.get(B, [])) if tag in T.get(D_, {}) and T[D_][tag].get('province_power', 0) >= 10]
            allowed = [c for w, c in links if (w > 0 or not snap)]
            pred = sum(d5(c['province_power']) for c in allowed)
            rec = tg.get(tag, {}).get('prev', 0.0)
            for kind in ('t_in', 't_out'):
                if any(c.get(kind, 0) > 0 for c in allowed):
                    res[(('snap' if snap else 'played'), kind, 'n')] += 1
                    res[(('snap' if snap else 'played'), kind, 'match')] += abs(pred - rec) < 5e-4
    if snap:
        for B, tg in T.items():
            for tag, c in tg.items():
                if c.get('t_in', 0) > 0 and 'max_pow' in c:
                    mp['n'] += 1
                    ex = round(c['max_pow'] - c.get('province_power', 0) - c.get('ship_power', 0) - c.get('prev', 0) - 5 * bool(c.get('has_capital')) - sum(m.get('power', 0) for m in as_list(c.get('modifier')) if isinstance(m, dict)), 3)
                    mp['decomp ok'] += ex == 0
print(sorted(res.items())); print(dict(mp))
