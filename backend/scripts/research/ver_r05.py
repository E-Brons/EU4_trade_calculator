"""Independent re-computation of the R05 headline claims (prev rule, threshold, weight gate, per-link truncation, MOR ship term)."""
import sys, json, collections, math
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
from common import as_list

G = json.load(open(Path(__file__).resolve().parents[2] / 'data' / 'tradenodes.json'))['nodes']
out = {n: [o['target'] for o in v['outgoing']] for n, v in G.items()}
inn = collections.defaultdict(list)
for n, ts in out.items():
    for i, t in enumerate(ts): inn[t].append((n, i))
PLAYED = {'S79', 'S80', 'U01', 'U02'}
def t3(x): return float(D(repr(float(x))).quantize(D('0.001'), rounding=ROUND_DOWN))
def d5(p): return float((D(repr(float(p))) / 5).quantize(D('0.001'), rounding=ROUND_DOWN))   # exact decimal division, then truncate
def dsum5(ps): return float((sum((D(repr(float(p))) for p in ps), D(0)) / 5).quantize(D('0.001'), rounding=ROUND_DOWN))
def ent(c): return isinstance(c, dict) and bool(set(c) - {'max_demand'})
def tags(n): return {t: c for t, c in n.items() if isinstance(c, dict) and t.upper() == t and len(t) <= 4}

tot = collections.Counter(); fails = collections.defaultdict(list)
var = collections.Counter(); multi = collections.Counter(); len_mis = collections.Counter()
below = []; above = []
single_gate = collections.Counter()
mor = collections.Counter()
for e in common.entries():
    sid = e['id']; played = sid in PLAYED
    ns = {n['definitions']: n for n in common.nodes(e)}
    T = {nid: tags(n) for nid, n in ns.items()}
    for B, n in ns.items():
        sp = as_list(n.get('steer_power'))
        len_mis[(len(sp) == len(out.get(B, [])))] += 1
    cands = set()
    for nid, tg in T.items():
        for tag, c in tg.items():
            if ent(c): cands.add((nid, tag))
            if c.get('province_power', 0) >= 10:
                for (B, i) in inn[nid]:
                    if B in ns: cands.add((B, tag))
            p = c.get('province_power', 0)
            if not played:
                if 9 <= p < 10: below.append(p)
                if 10 <= p < 11: above.append(p)
    for (B, tag) in cands:
        rec = T[B].get(tag, {}).get('prev', 0.0)
        sp = as_list(ns[B].get('steer_power'))
        links = []  # (weight, pD)
        for i, D_ in enumerate(out.get(B, [])):
            c = T.get(D_, {}).get(tag)
            if c is None: continue
            p = c.get('province_power', 0.0)
            if p >= 10: links.append((sp[i] if i < len(sp) else 0, p, D_))
        gated = sum(d5(p) for w, p, _ in links if w > 0)
        ungated = sum(d5(p) for w, p, _ in links)
        g = 'played' if played else 'snap'
        tot[g] += 1
        tot[(g, 'gate ok')] += abs(gated - rec) < 0.0005
        tot[(g, 'nogate ok')] += abs(ungated - rec) < 0.0005
        if not played:
            allp = [p for w, p, _ in links if w > 0]
            for name, fn in (('sum trunc3(p/5)', lambda ps: sum(d5(p) for p in ps)), ('trunc3(sum/5)', lambda ps: dsum5(ps)),
                             ('round3(sum/5)', lambda ps: round(sum(ps) / 5 + 1e-12, 3)), ('sum/5', lambda ps: sum(ps) / 5)):
                var[name] += abs(fn(allp) - rec) < 1e-6
                if len(allp) >= 2: multi[name] += abs(fn(allp) - rec) < 1e-6
            if len(allp) >= 2: multi['n'] += 1
        if played and abs(gated - rec) >= 0.0005: fails[sid].append((B, tag, rec, gated))
        # MOR ship term
        if played and tag == 'MOR':
            shp = sum(T[D_][tag].get('ship_power', 0) * 0.25 / 5 for w, p, D_ in links if T.get(D_, {}).get(tag))  # ungated like the claim (link allowed)
            mor['n'] += 1
            mor['nogate+ships ok'] += abs(ungated + shp - rec) < 0.0006
            mor['nogate ok'] += abs(ungated - rec) < 0.0006
            mor['gate+ships ok'] += abs(gated + sum(T[D_][tag].get('ship_power', 0) * 0.25 / 5 for w, p, D_ in links if w > 0) - rec) < 0.0006
print('steer_power length == number of outgoing links:', dict(len_mis))
print('snap candidates', tot['snap'], 'gate ok', tot[('snap', 'gate ok')], 'nogate ok', tot[('snap', 'nogate ok')])
print('played candidates', tot['played'], 'gate ok', tot[('played', 'gate ok')], 'nogate ok', tot[('played', 'nogate ok')])
print('variants (snapshots, gated set, exact):', dict(var)); print('multi-link', dict(multi))
print('largest province_power<10 in [9,10):', max(below), ' smallest >=10 in [10,11):', min(above))
print('MOR played candidates', dict(mor))
for s, f in fails.items(): print(s, 'gated fails', len(f), f[:3])
