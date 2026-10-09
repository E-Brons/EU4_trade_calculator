"""R03 rules A and B on the Venice saves (same logic as r03_final_ab.py): nodes where A and B differ and which one the recorded pull_power follows; plus the controlled flip of VEN (steering -> idle -> steering)."""
import sys
sys.path.insert(0, 'scripts/research'); sys.path.insert(0, '.')
import venice_load as V
from collections import defaultdict, Counter
from app.parsing.tradenodes import load_trade_graph
G = load_trade_graph(); DOWN = {}
def down(n):
    if n not in DOWN:
        s = set()
        for t in G.outgoing(n): s.add(t); s |= down(t)
        DOWN[n] = s
    return DOWN[n]
for n in G.nodes: down(n)
def f(x):
    try: return float(x)
    except Exception: return 0.0

tot = Counter(); diffs = []
for p in V.files():
    nodes = V.nodes(p); ents = {}
    for n in nodes:
        for t, d in n.items():
            if isinstance(d, dict) and len(t) <= 4 and t.upper() == t and set(d) - {'max_demand'}: ents[(n['definitions'], t)] = d
    coll = defaultdict(set); st = defaultdict(set)
    for (node, t), d in ents.items():
        if 'total' in d or d.get('has_capital'): coll[t].add(node)
        if 'type' in d: st[t].add(node)
    c = Counter()
    for n in nodes:
        nid = n['definitions']
        if n.get('pull_power') is None: continue
        pa = pb = 0.0; extra = []
        for (node, t), d in ents.items():
            if node != nid: continue
            eff = f(d.get('val')) - f(d.get('t_out')) + f(d.get('t_in'))
            ch = 'total' in d or bool(d.get('has_capital')); s = 'type' in d
            a = s or (not ch and bool(coll[t] & down(nid)))
            b = s or (not ch and bool((coll[t] | st[t]) & down(nid)))
            pa += eff * a; pb += eff * b
            if b and not a: extra.append((t, round(eff, 3)))
        rp = f(n['pull_power']); c['nodes'] += 1
        c['A ok'] += abs(pa - rp) <= 0.0105; c['B ok'] += abs(pb - rp) <= 0.0105
        if abs(pa - pb) > 0.0105:
            c['A!=B'] += 1; diffs.append((p.stem[6:], nid, extra, round(pa, 3), round(pb, 3), rp))
    tot.update(c)
    print(p.stem[6:], dict(c))
print('TOTAL', dict(tot))
for d in diffs[:12]: print(d)
