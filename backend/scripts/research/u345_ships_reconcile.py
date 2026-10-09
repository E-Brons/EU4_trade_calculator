"""U03-U05 (and S79/S80 for comparison): reconcile protect-mission fleets with node light_ship/ship_power; f = ship_power/base."""
import sys, json, itertools, pickle
sys.path.insert(0, 'scripts/research')
import common, u345_ships_load as L
from collections import Counter, defaultdict
A = common.as_list
BASE = {k: v['trade_power'] for k, v in json.load(open('data/game/light_ships.json'))['ships'].items()}

def ship_types(f):
    return Counter(s['type'] for s in A(f.get('ship')) if isinstance(s, dict))

def analyse(e):
    nodes = common.nodes(e); order = [n['definitions'] for n in nodes]
    ent = {}
    for n in nodes:
        for tag, c in n.items():
            if isinstance(c, dict) and c.get('light_ship'):
                ent[(tag, n['definitions'])] = (int(c['light_ship']), float(c['ship_power']))
    cs = common.block(e, 'countries')
    fleets = defaultdict(list); nps = {}
    for tag, c in cs.items():
        if not isinstance(c, dict): continue
        nps[tag] = c.get('num_ships_protecting_trade')
        for f in A(c.get('navy')):
            if not isinstance(f, dict): continue
            m = f.get('mission'); pm = m.get('protect_mission') if isinstance(m, dict) else None
            if not isinstance(pm, dict): continue
            ty = ship_types(f)
            if not any(t in BASE for t in ty): continue
            fleets[(tag, order[int(pm['node']) - 1])].append(dict(name=f.get('name'), types=ty, omw=pm.get('on_my_way', '<absent>'),
                                                                 mp=f.get('movement_progress'), path='path' in f, cyc=pm.get('current_cycle_begin'),
                                                                 leader='leader' in f))
    rows = []
    for key in sorted(set(ent) | set(fleets)):
        fl = fleets.get(key, []); en = ent.get(key)
        fits = []
        for r in range(len(fl) + 1):
            for sub in itertools.combinations(range(len(fl)), r):
                ty = Counter()
                for i in sub: ty.update({t: n for t, n in fl[i]['types'].items() if t in BASE})
                nl = sum(ty.values()); pb = sum(BASE[t] * n for t, n in ty.items())
                if en and en[0] == nl and nl > 0 and pb > 0 and abs(en[1] / pb - round(en[1] / pb, 2)) < 0.0015:
                    fits.append((sub, nl, pb, en[1] / pb))
        rows.append((key, en, fl, fits))
    return dict(id=e['id'], date=e['date'], rows=rows, nps=nps, ent=ent, fleets=fleets)

if __name__ == '__main__':
    out = {}
    for e in L.OLD + L.NEW:
        r = analyse(e); out[e['id']] = r
        rows = r['rows']
        uniq = [x for x in rows if x[1] and len(x[3]) == 1]
        amb = [x for x in rows if x[1] and len(x[3]) > 1]
        nofit = [x for x in rows if x[1] and not x[3]]
        nonentry = [x for x in rows if not x[1]]
        fs = Counter(round(x[3][0][3], 3) for x in uniq)
        print(f"== {e['id']} ({e['date']}): entries {len(r['ent'])}, unique fit {len(uniq)}, ambiguous {len(amb)}, no fit {len(nofit)}, fleet-nodes without entry {len(nonentry)}; f histogram {dict(fs)}")
        for x in nofit: print('   NOFIT', x[0], x[1], [(f['name'], dict(f['types']), f['omw']) for f in x[2]])
        for x in amb: print('   AMBIG', x[0], x[1], [(f['name'], dict(f['types']), f['omw']) for f in x[2]], [(s[0], round(s[3], 3)) for s in x[3]])
        for x in nonentry: print('   FLEET WITHOUT ENTRY', x[0], [(f['name'], dict(f['types']), f['omw'], f['mp'], f['path'], f['cyc']) for f in x[2]])
        # counted-vs-uncounted by on_my_way
        cnt = Counter(); 
        for key, en, fl, fits in rows:
            if not en:
                for f in fl: cnt[('uncounted', f['omw'])] += 1
        print('   on_my_way of fleets in entry-less nodes:', dict(cnt))
        tur = r['nps'].get('TUR'); tur_ent = sum(v[0] for (t, n), v in r['ent'].items() if t == 'TUR')
        tur_fl = sum(sum(n for t, n in f['types'].items() if t in BASE) for (t, nd), fl in r['fleets'].items() if t == 'TUR' for f in fl)
        print(f'   TUR: num_ships_protecting_trade={tur}, sum node light_ship={tur_ent}, light ships on protect missions={tur_fl}')
        # all countries: nps vs fleets vs entries
        d = Counter()
        for tag, v in r['nps'].items():
            fl = sum(sum(n for t, n in f['types'].items() if t in BASE) for (t2, nd), ff in r['fleets'].items() if t2 == tag for f in ff)
            en = sum(v2[0] for (t2, nd), v2 in r['ent'].items() if t2 == tag)
            if v is None and not fl: continue
            d[(int(v or 0) == fl, int(v or 0) == en)] += 1
        print('   countries (nps==fleets?, nps==entries?):', dict(d))
    pickle.dump({k: {kk: vv for kk, vv in v.items() if kk != 'rows'} for k, v in out.items()}, open('/tmp/eu4research/cache/u345_ships_reconcile.pkl', 'wb'))
