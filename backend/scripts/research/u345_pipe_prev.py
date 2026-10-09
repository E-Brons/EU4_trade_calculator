"""R05 prev rule (per-link trunc3(province_power/5), threshold 10, steer-weight gate) and the MOR ship term, per save, incl. U03/U04/U05.
Run from backend/: .venv/bin/python scripts/research/u345_pipe_prev.py"""
import sys, json, collections
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list

G = json.load(open('data/tradenodes.json'))['nodes']
out = {n: [o['target'] for o in v['outgoing']] for n, v in G.items()}
inn = collections.defaultdict(list)
for n, ts in out.items():
    for i, t in enumerate(ts): inn[t].append((n, i))
NEW = [dict(id='U03', file='U03_TUR.1691.01.09.eu4', tag='TUR', date='1691.1.9', kind='user_case'),
       dict(id='U04', file='U04_TUR.1691.11.01.eu4', tag='TUR', date='1691.11.1', kind='user_case'),
       dict(id='U05', file='U05_TUR.1693.04.15.eu4', tag='TUR', date='1693.4.15', kind='user_case')]
PLAYED = {'S79', 'S80', 'U01', 'U02', 'U03', 'U04', 'U05'}
def d5(p): return float((D(repr(float(p))) / 5).quantize(D('0.001'), rounding=ROUND_DOWN))
def ent(c): return isinstance(c, dict) and bool(set(c) - {'max_demand'})
def tags(n): return {t: c for t, c in n.items() if isinstance(c, dict) and t.upper() == t and len(t) <= 4}

def per_save(e, ship_k=0.25):
    ns = {n['definitions']: n for n in common.nodes(e)}
    T = {nid: tags(n) for nid, n in ns.items()}
    cands = set()
    for nid, tg in T.items():
        for tag, c in tg.items():
            if ent(c): cands.add((nid, tag))
            if c.get('province_power', 0) >= 10:
                for (B, i) in inn[nid]:
                    if B in ns: cands.add((B, tag))
    r = collections.Counter(); fails = []; allfails = []
    for (B, tag) in cands:
        rec = T[B].get(tag, {}).get('prev', 0.0)
        sp = as_list(ns[B].get('steer_power'))
        links = []
        for i, Dn in enumerate(out.get(B, [])):
            c = T.get(Dn, {}).get(tag)
            if c is None: continue
            p = c.get('province_power', 0.0)
            if p >= 10: links.append((sp[i] if i < len(sp) else 0, p, c.get('ship_power', 0.0), Dn))
        gated = sum(d5(p) for w, p, s, _ in links if w > 0)
        ungated = sum(d5(p) for w, p, s, _ in links)
        shp_g = sum(s * ship_k / 5 for w, p, s, _ in links if w > 0)
        r['cands'] += 1
        g_ok = abs(gated - rec) < 0.0005; u_ok = abs(ungated - rec) < 0.0005
        r['gate_ok'] += g_ok; r['nogate_ok'] += u_ok; r['either_ok'] += (g_ok or u_ok)
        if not g_ok:
            s_ok = abs(gated + shp_g - rec) < 0.0006
            r['gate_fail'] += 1; r['gate_fail_explained_by_nogate'] += u_ok; r['gate_fail_explained_by_ship'] += s_ok
            r['gate_fail_has_downstream_ships'] += any(s > 0 for w, p, s, _ in links if w > 0)
            fails.append((B, tag, rec, round(gated, 3), round(ungated, 3), round(shp_g, 3)))
        if any(s > 0 for w, p, s, _ in links if w > 0):
            r['with_ship_cands'] += 1; r['with_ship_gate_ok'] += g_ok
            r['with_ship_shipterm_ok'] += abs(gated + shp_g - rec) < 0.0006
            r[f'ship_tag_{tag}'] += 1
        zero_w = [1 for w, p, s, _ in links if not w > 0]
        r['links_pD_ge10'] += len(links); r['links_pD_ge10_w0'] += len(zero_w)
        r['w0_links_with_prev_contrib'] += 0
    return r, fails

if __name__ == '__main__':
    ents = common.entries() + NEW
    want = [e for e in ents if e['id'] in PLAYED or e['id'] in ('S14', 'S42', 'S01')]
    rows = {}
    for e in want:
        r, fails = per_save(e)
        rows[e['id']] = (r, fails)
        print(e['id'], e['date'], {k: v for k, v in r.items() if not k.startswith('ship_tag_')})
        print('   first gate fails:', fails[:6])
        print('   tags of entries with downstream ships:', {k[9:]: v for k, v in r.items() if k.startswith('ship_tag_')})
    # all start snapshots aggregate
    agg = collections.Counter()
    for e in ents:
        if e['id'] in PLAYED: continue
        r, _ = per_save(e); agg.update({k: v for k, v in r.items() if not k.startswith('ship_tag_')})
    print('ALL START SNAPSHOTS', dict(agg))
