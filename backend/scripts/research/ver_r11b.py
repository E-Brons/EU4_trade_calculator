"""R11 verification part 2: fleet-level counts, type totals, leader/home/tcr/home-collector statistics for the f != 1 claim, caps."""
import sys, json, itertools
sys.path.insert(0, 'scripts/research')
import common
from collections import Counter, defaultdict

A = common.as_list
BASE = {k: v['trade_power'] for k, v in json.load(open('data/game/light_ships.json'))['ships'].items()}
TN = json.load(open('data/tradenodes.json'))['nodes']
prov2node = {}
for nid, nd in TN.items():
    for p in nd['member_provinces']:
        prov2node[p] = nid


def is_tag(k, v):
    return isinstance(v, dict) and 2 <= len(k) <= 4 and k.upper() == k


types_all = Counter()
groups = []  # (sid, tag, node, entry(l,p,cap,tcr), fleets[list])
for sid in ('S79', 'S80'):
    e = [x for x in common.entries() if x['id'] == sid][0]
    nodes = common.nodes(e); order = [n['definitions'] for n in nodes]
    cs = common.block(e, 'countries')
    ent = {}
    for n in nodes:
        for k, c in n.items():
            if is_tag(k, c) and 'light_ship' in c:
                ent[(k, n['definitions'])] = dict(l=int(c['light_ship']), p=float(c['ship_power']), cap=bool(c.get('has_capital')),
                                                  coll='total' in c, tcr=bool(n.get('trade_company_region')))
    by = defaultdict(list)
    for tag, c in cs.items():
        if not isinstance(c, dict):
            continue
        for f in A(c.get('navy')):
            if not isinstance(f, dict):
                continue
            m = f.get('mission'); pm = m.get('protect_mission') if isinstance(m, dict) else None
            if not isinstance(pm, dict):
                continue
            ships = [s for s in A(f.get('ship')) if isinstance(s, dict)]
            for s in ships:
                types_all[s.get('type')] += 1
            by[(tag, order[int(pm['node']) - 1])].append(dict(name=f.get('name'), onway='on_my_way' in pm, ships=ships, leader='leader' in f))
    for key in set(by) | set(ent):
        groups.append((sid, key[0], key[1], ent.get(key), by.get(key, [])))

print('type counts over protect-mission fleets S79+S80:', dict(types_all))

# fleet-level counting: subset-sum uniqueness for each group
def lightstats(fs):
    cnt = Counter(s['type'] for f in fs for s in f['ships'] if s['type'] in BASE)
    return sum(cnt.values()), sum(BASE[t] * k for t, k in cnt.items())

fleet_total = 0; counted = 0; uncounted = []; ambiguous = []; fvals = {}
for sid, tag, node, en, fl in groups:
    fl_l = [f for f in fl]
    n = len(fl_l)
    if n > 14:
        print('SKIP big group', sid, tag, node, n); continue
    fits = []
    for r in range(0, n + 1):
        for sub in itertools.combinations(range(n), r):
            l, b = lightstats([fl_l[i] for i in sub])
            if en is None:
                ok = (len(sub) == 0)
            else:
                ok = (l == en['l'] and b > 0 and en['p'] / b in [en['p'] / b] and abs(round(en['p'] / b, 3) - round(en['p'] / b, 3)) < 1e-9 and round(en['p'] / b, 3) in (1.0, 1.05, 1.1, 1.2))
            if ok:
                fits.append(sub)
    if en is not None and not fits:
        print('NO FIT', sid, tag, node, en)
    if en is not None and len(fits) > 1:
        ambiguous.append((sid, tag, node, fits))
    if en is None:
        # entry absent: all fleets uncounted
        for f in fl_l:
            if lightstats([f])[0] > 0:
                fleet_total += 1; uncounted.append((sid, tag, node, f['name'], f['onway']))
        continue
    if len(fits) == 1:
        sub = fits[0]
        for i, f in enumerate(fl_l):
            if lightstats([f])[0] == 0:
                continue
            fleet_total += 1
            if i in sub:
                counted += 1
            else:
                uncounted.append((sid, tag, node, f['name'], f['onway']))
print('fleets with light ships in uniquely-fitted groups:', fleet_total, 'counted', counted, 'uncounted', len(uncounted))
print('uncounted:', Counter(u[4] for u in uncounted))
for u in uncounted:
    print('  ', u)
print('counted fleets all with on_my_way key? -> see counted', counted, 'vs fleets with key:',
      sum(1 for g in groups for f in g[4] if f['onway'] and lightstats([f])[0] > 0))
print('ambiguous groups:', ambiguous)

# f statistics for uniquely-fitted entries
rows = []
for sid, tag, node, en, fl in groups:
    if en is None:
        continue
    n = len(fl)
    if n > 14:
        continue
    fits = []
    for r in range(1, n + 1):
        for sub in itertools.combinations(range(n), r):
            l, b = lightstats([fl[i] for i in sub])
            if l == en['l'] and b > 0 and round(en['p'] / b, 3) in (1.0, 1.05, 1.1, 1.2):
                fits.append(sub)
    if len(fits) != 1:
        continue
    sub = fits[0]; sel = [fl[i] for i in sub]
    l, b = lightstats(sel)
    f = round(en['p'] / b, 3)
    all_home_in = all(prov2node.get(s.get('home')) == node for fl_ in sel for s in fl_['ships'] if s['type'] in BASE)
    none_home_in = not any(prov2node.get(s.get('home')) == node for fl_ in sel for s in fl_['ships'] if s['type'] in BASE)
    rows.append(dict(sid=sid, tag=tag, node=node, f=f, leader=any(x['leader'] for x in sel), all_home=all_home_in, none_home=none_home_in,
                     tcr=en['tcr'], cap=en['cap'], coll=en['coll'], l=en['l']))
print('uniquely fitted entries:', len(rows), Counter(r['f'] for r in rows))
one = [r for r in rows if r['f'] == 1.0]; non = [r for r in rows if r['f'] != 1.0]
print('leader among f!=1:', sum(r['leader'] for r in non), 'of', len(non), '| among f=1:', sum(r['leader'] for r in one), 'of', len(one))
print('all ships homed in node: f!=1', sum(r['all_home'] for r in non), 'none', sum(r['none_home'] for r in non), 'mixed', sum((not r['all_home']) and (not r['none_home']) for r in non),
      '| f=1 all homed', sum(r['all_home'] for r in one))
print('tcr: f!=1', sum(r['tcr'] for r in non), 'of', len(non), '| f=1', sum(r['tcr'] for r in one))
print('home(has_capital) collecting: f!=1', sum(r['cap'] and r['coll'] for r in non), '| f=1 per save', Counter(r['sid'] for r in one if r['cap'] and r['coll']))
print('home node with ships (has_capital) f=1 all:', sum(r['cap'] for r in one))
print('max light per entry (desc):', sorted(((r['l'], r['sid'], r['tag'], r['node']) for r in rows), reverse=True)[:8])
# DAN/SPA by node
for t in ('DAN', 'SPA'):
    print(t, [(r['sid'], r['node'], r['f']) for r in rows if r['tag'] == t])
