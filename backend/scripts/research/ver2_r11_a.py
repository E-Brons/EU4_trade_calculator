"""Second-pass verification of R11 update: independent fleet/entry reconciliation and f histogram over all 85 saves."""
import sys, json, itertools, pickle
sys.path.insert(0, 'scripts/research')
import common
from collections import Counter, defaultdict
A = common.as_list
BASE = {k: v['trade_power'] for k, v in json.load(open('data/game/light_ships.json'))['ships'].items()}

def entries_with_ships(e):
    out = {}
    nodes = common.nodes(e)
    order = [n['definitions'] for n in nodes]
    for n in nodes:
        for tag, c in n.items():
            if isinstance(c, dict) and 'light_ship' in c:
                out[(tag, n['definitions'])] = (int(c['light_ship']), float(c.get('ship_power', 0)), c)
    return order, out

def fleets_of(e, order):
    cs = common.block(e, 'countries')
    res = defaultdict(list)
    allf = []
    for tag, c in cs.items():
        if not isinstance(c, dict): continue
        for f in A(c.get('navy')):
            if not isinstance(f, dict): continue
            m = f.get('mission'); pm = m.get('protect_mission') if isinstance(m, dict) else None
            if not isinstance(pm, dict): continue
            ty = Counter(s.get('type') for s in A(f.get('ship')) if isinstance(s, dict))
            lt = {t: n for t, n in ty.items() if t in BASE}
            rec = dict(tag=tag, id=f.get('id'), name=f.get('name'), light=lt, types=dict(ty), omw=pm.get('on_my_way', '<absent>'),
                       leader=f.get('leader'), node=order[int(pm['node']) - 1])
            res[(tag, rec['node'])].append(rec)
            allf.append(rec)
    return cs, res, allf

def fit(en, fl):
    """all subsets of fleets whose light-ship count equals the entry's light_ship; returns list of (subset, base_sum, f)"""
    fits = []
    for r in range(1, len(fl) + 1):
        for sub in itertools.combinations(range(len(fl)), r):
            n = sum(sum(fl[i]['light'].values()) for i in sub)
            if n != en[0]: continue
            b = sum(BASE[t] * k for i in sub for t, k in fl[i]['light'].items())
            if b > 0: fits.append((sub, b, en[1] / b))
    return fits

if __name__ == '__main__':
    res = {}
    for e in common.entries():
        order, ent = entries_with_ships(e)
        if not ent: continue
        cs, fl, allf = fleets_of(e, order)
        rows = []
        for key, en in ent.items():
            fits = fit(en, fl.get(key, []))
            # distinct f values among fits (rounded)
            fs = sorted({round(x[2], 4) for x in fits})
            rows.append((key, en[:2], fits, fs))
        res[e['id']] = dict(date=e['date'], rows=rows, fl=fl, allf=allf, ent=ent)
        uniq = [r for r in rows if len({round(x[2], 4) for x in r[2]}) == 1 and r[2]]
        amb = [r for r in rows if len({round(x[2], 4) for x in r[2]}) > 1]
        nofit = [r for r in rows if not r[2]]
        print(e['id'], e['date'], 'entries', len(ent), 'unique f', len(uniq), 'ambiguous f', len(amb), 'nofit', len(nofit),
              dict(Counter(round(r[2][0][2], 3) for r in uniq)))
        for r in nofit: print('   NOFIT', r[0], r[1])
        for r in amb: print('   AMBIG', r[0], r[1], r[3])
    pickle.dump({k: dict(date=v['date'], rows=[(r[0], r[1], [(x[1], x[2]) for x in r[2]], r[3]) for r in v['rows']]) for k, v in res.items()},
                open('/tmp/eu4research/ver2_r11_a.pkl', 'wb'))
