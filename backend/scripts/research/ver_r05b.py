"""R05 extra checks: played-save single-link gate table; ship term specificity to MOR; MOR counts over all saves."""
import sys, json, collections
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
def d5(p): return float((D(repr(float(p))) / 5).quantize(D('0.001'), rounding=ROUND_DOWN))
def ent(c): return isinstance(c, dict) and bool(set(c) - {'max_demand'})
def tags(n): return {t: c for t, c in n.items() if isinstance(c, dict) and t.upper() == t and len(t) <= 4}
PLAYED = {'S79', 'S80', 'U01', 'U02'}
single = collections.Counter(); ship = collections.Counter(); mor_all = collections.Counter(); mor_shipvals = collections.Counter()
nonmor_examples = []
for e in common.entries():
    sid = e['id']; played = sid in PLAYED
    ns = {n['definitions']: n for n in common.nodes(e)}; T = {k: tags(n) for k, n in ns.items()}
    cands = set()
    for nid, tg in T.items():
        for tag, c in tg.items():
            if ent(c): cands.add((nid, tag))
            if c.get('province_power', 0) >= 10:
                for (B, i) in inn[nid]:
                    if B in ns: cands.add((B, tag))
    for (B, tag) in cands:
        rec = T[B].get(tag, {}).get('prev', 0.0); sp = as_list(ns[B].get('steer_power'))
        links = [(sp[i] if i < len(sp) else 0, T[D_][tag]['province_power'], T[D_][tag].get('ship_power', 0.0)) for i, D_ in enumerate(out.get(B, []))
                 if tag in T.get(D_, {}) and T[D_][tag].get('province_power', 0) >= 10]
        ung = sum(d5(p) for w, p, s in links)
        if played and len(links) == 1:
            w, p, s = links[0]; single[(w > 0, rec > 0)] += 1
        shp = sum(s * 0.25 / 5 for w, p, s in links)
        has_ship = any(s > 0 for w, p, s in links)
        if tag == 'MOR':
            mor_all[('played' if played else 'snap', 'with', abs(ung + shp - rec) < 6e-4)] += 1
            mor_all[('played' if played else 'snap', 'without', abs(ung - rec) < 6e-4)] += 1
        if played and tag != 'MOR' and has_ship:
            ship['n'] += 1; ship['ungated matches (no ship term)'] += abs(ung - rec) < 6e-4
            ship['ungated + ship term matches'] += abs(ung + shp - rec) < 6e-4
            if abs(ung - rec) >= 6e-4: nonmor_examples.append((sid, B, tag, rec, ung, shp))
print('played single-link (weight>0?, propagated?):', dict(single))
print('MOR all saves:', dict(mor_all))
print('non-MOR played entries with downstream ship_power>0 on an allowed link:', dict(ship), nonmor_examples[:5])
