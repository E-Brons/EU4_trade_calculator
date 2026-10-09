"""Independent verification: quoted province rows (R13 C-02/C-03, R09 C-06) and M classes."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
E = {e['id']: e for e in common.entries()}
pr = common.block(E['S01'], 'provinces'); ns = {n['definitions']: n for n in common.nodes(E['S01'])}
def row(pid):
    p = pr[pid]; dev = p['base_tax'] + p['base_production'] + p['base_manpower']
    return dict(name=p.get('name'), owner=p.get('owner'), ctrl=p.get('controller'), node=p.get('trade'), dev=dev, cot=p.get('center_of_trade'), aut=p.get('local_autonomy'), tp=p.get('trade_power'))
for pid in ['-514', '-2058', '-518', '-2087', '-2067', '-4506', '-1', '-23', '-568', '-4457']:
    r = row(pid); flat = {None: 0, 1: 5, 2: 10, 3: 25}[r['cot']]; base = 0.2 * r['dev'] + flat; a = (r['aut'] or 0)
    print(pid, r, 'base', round(base, 3), 'implied M (aut factor 0.005)', round(r['tp'] / (base * (1 - 0.005 * a)), 4) if base else None)
# MER at gujarat
g = [p for p in pr.values() if isinstance(p, dict) and p.get('trade') == 'gujarat']
mer_own = sum(p['trade_power'] for p in g if p.get('owner') == 'MER'); mer_ctl = sum(p['trade_power'] for p in g if p.get('controller') == 'MER')
print('gujarat MER owned sum', round(mer_own, 3), 'controlled', round(mer_ctl, 3), 'entry province_power', ns['gujarat']['MER']['province_power'], 'p_pow', ns['gujarat']['p_pow'], 'total', ns['gujarat']['total'])
print('gujarat total - sum(val)', round(ns['gujarat']['total'] - sum(v.get('val', 0) for k, v in ns['gujarat'].items() if re.match(r'^[A-Z0-9]{2,4}$', k) and isinstance(v, dict)), 3))
# M classes: provinces with positive base, controller == owner, cot/aut known
cls = collections.Counter(); tot = 0
for pid, p in pr.items():
    if not isinstance(p, dict) or 'trade_power' not in p or p.get('controller') != p.get('owner') or not p.get('owner'): continue
    dev = p['base_tax'] + p['base_production'] + p['base_manpower']; flat = {None: 0, 1: 5, 2: 10, 3: 25}.get(p.get('center_of_trade'), None)
    if flat is None: continue
    base = 0.2 * dev + flat
    if base <= 0: continue
    a = p.get('local_autonomy') or 0; M = p['trade_power'] / (base * (1 - 0.005 * a)); cls[round(M, 1)] += 1; tot += 1
print('S01 provinces used', tot, sorted(cls.items(), key=lambda x: -x[1])[:12])
# fraction of provinces in cls that reproduce exactly with M in {1.2,1.45,...} is not tested here; only the shape:
# aut factor: least squares of implied M vs autonomy among CoT0 provinces with M~1.2
import math
pts = []
for pid, p in pr.items():
    if not isinstance(p, dict) or 'trade_power' not in p or p.get('controller') != p.get('owner') or not p.get('owner'): continue
    if p.get('center_of_trade'): continue
    dev = p['base_tax'] + p['base_production'] + p['base_manpower']
    if dev < 6: continue
    pts.append(((p.get('local_autonomy') or 0), p['trade_power'] / (0.2 * dev)))
by = collections.defaultdict(list)
for a, m in pts: by[a].append(m)
print('implied M (no CoT, dev>=6) by autonomy (median):', {a: round(sorted(v)[len(v)//2], 4) for a, v in sorted(by.items())[:8]})
