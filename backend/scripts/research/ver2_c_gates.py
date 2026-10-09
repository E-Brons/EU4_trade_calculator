"""Second pass: R05 gate variants and the polynesia_node misses, independent code. Run from backend/."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from ver2_c_identities import OUT, TAG, lst, num, tr3, entries_of, is_entry

def analyse(e):
    nl = common.nodes(e); order = [n['definitions'] for n in nl]; ns = {n['definitions']: n for n in nl}
    E = {k: entries_of(v) for k, v in ns.items()}
    inc = {}
    for to, n in ns.items():
        for i in lst(n.get('incoming')):
            if isinstance(i, dict):
                inc[(order[int(i['from']) - 1], to)] = num(i.get('value')) or 0.0
    rows = []
    for B in ns:
        outs = OUT.get(B, []); sp = [num(x) for x in lst(ns[B].get('steer_power'))]
        cand = {t for t, x in E[B].items() if is_entry(x)}
        for Dn in outs:
            for t, x in E.get(Dn, {}).items():
                if (num(x.get('province_power')) or 0) >= 10: cand.add(t)
        for t in cand:
            rec = num(E[B].get(t, {}).get('prev')) or 0.0
            links = []
            for i, Dn in enumerate(outs):
                x = E.get(Dn, {}).get(t)
                if x and (num(x.get('province_power')) or 0) >= 10:
                    links.append((i, Dn, tr3(x['province_power'], div=5), sp[i] if i < len(sp) else None, (B, Dn) in inc, inc.get((B, Dn), 0.0) > 0))
            s = lambda f: sum(l[2] for l in links if f(l))
            rows.append(dict(B=B, t=t, rec=rec, links=links, ung=s(lambda l: True), gw=s(lambda l: l[3] and l[3] > 0), g1=s(lambda l: l[4]), g2=s(lambda l: l[5])))
    return rows

ok = lambda a, b: abs(a - b) <= 0.0005
if __name__ == '__main__':
    pool = {e['id']: e for e in common.entries()}
    for sid in sys.argv[1:] or ['S79', 'U03']:
        rows = analyse(pool[sid])
        q = [r for r in rows if r['links']]
        z = [r for r in q if any(l[3] == 0 for l in r['links'])]          # has a qualifying link with weight 0
        print(sid, 'candidates', len(rows), 'with qualifying link', len(q), 'with a weight-0 qualifying link', len(z))
        for nm, k in (('ungated', 'ung'), ('weight-gate', 'gw'), ('incoming-exists gate', 'g1'), ('incoming>0 gate', 'g2')):
            print('   ', nm, 'exact over candidates', sum(ok(r[k], r['rec']) for r in rows), '/', len(rows), '| over qualifying', sum(ok(r[k], r['rec']) for r in q), '/', len(q), '| over weight-0 group', sum(ok(r[k], r['rec']) for r in z), '/', len(z))
        miss = [r for r in rows if not ok(r['ung'], r['rec'])]
        print('    ungated misses:', [(r['B'], r['t'], r['rec'], round(r['ung'], 3)) for r in miss])
        print('    weights at polynesia_node:', ns if False else '')
