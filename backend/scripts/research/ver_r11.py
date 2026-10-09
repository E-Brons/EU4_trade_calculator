"""Independent verification of R11 response_1 (does not reuse r11_r14_*.py logic).

Approach: for every save, every trade-node entry with `light_ship`; every fleet of that country whose
mission.protect_mission.node (1-based) names the node. A fleet is 'live' if its protect_mission has an on_my_way key
(author's finding is checked, not assumed): we test several candidate counting rules against the stored light_ship.
"""
import sys, json
sys.path.insert(0, 'scripts/research')
import common
from collections import Counter, defaultdict

A = common.as_list
BASE = {k: v['trade_power'] for k, v in json.load(open('data/game/light_ships.json'))['ships'].items()}
TN = json.load(open('data/tradenodes.json'))['nodes']


def fleets_of(country):
    out = []
    for f in A(country.get('navy')):
        if not isinstance(f, dict):
            continue
        m = f.get('mission')
        pm = m.get('protect_mission') if isinstance(m, dict) else None
        ships = [s for s in A(f.get('ship')) if isinstance(s, dict)]
        out.append(dict(name=f.get('name'), pm=pm if isinstance(pm, dict) else None, ships=ships, leader=('leader' in f), raw=f))
    return out


def is_tag(k, v):
    return isinstance(v, dict) and 2 <= len(k) <= 4 and k.upper() == k


start_entries = 0
all_ent = []  # (save, tag, node, light_ship, ship_power)
per_save = {}
for e in common.entries():
    nodes = common.nodes(e)
    order = [n['definitions'] for n in nodes]
    ents = []
    for n in nodes:
        for k, c in n.items():
            if is_tag(k, c) and 'light_ship' in c:
                ents.append((k, n['definitions'], int(c['light_ship']), float(c.get('ship_power', 0))))
    if ents:
        per_save[e['id']] = (e, order, ents)
    elif e['kind'] == 'start' if 'kind' in e else True:
        pass
    all_ent.append((e['id'], len(ents)))

print('saves with light_ship entries:', {s: len(v[2]) for s, v in per_save.items()})
print('entries with light_ship in all others:', sum(n for s, n in all_ent if s not in per_save), '(must be 0)')

# ---- per save reconciliation
f_hist = Counter(); f_rows = []
unresolved = []
total_entries = 0
all_fleet_stats = Counter()
morales = []
strength_ships = 0; light_on_missions = 0
nps_diff = []
tur_report = None
maxlight = (0, None)
inland_ent = 0; inland_fleets = 0
nonlight_cases = []
for sid, (e, order, ents) in per_save.items():
    cs = common.block(e, 'countries')
    byentry = {(t, n): (l, p) for t, n, l, p in ents}
    tags = {t for t, _, _, _ in ents}
    # include every country with any protect mission for counting the fleet stats
    for tag, c in cs.items():
        if not isinstance(c, dict):
            continue
        fl = fleets_of(c)
        pmf = [f for f in fl if f['pm']]
        if not pmf and tag not in tags:
            continue
        light_mission = 0
        by_node = defaultdict(list)
        for f in pmf:
            nid = int(f['pm']['node'])
            nname = order[nid - 1]
            by_node[nname].append(f)
            if TN[nname]['inland']:
                inland_fleets += 1
            for s in f['ships']:
                if s.get('type') in BASE:
                    light_mission += 1
                    morales.append(float(s['morale']))
                    if 'strength' in s:
                        strength_ships += 1
        nps = c.get('num_ships_protecting_trade')
        node_sum = sum(l for (t, n), (l, p) in byentry.items() if t == tag)
        if tag in tags or pmf:
            nps_diff.append((sid, tag, nps, node_sum, light_mission))
        for nname, flist in by_node.items():
            # counting rule under test: fleets having an on_my_way key
            live = [f for f in flist if 'on_my_way' in f['pm']]
            def agg(fs):
                cnt = Counter()
                for f in fs:
                    for s in f['ships']:
                        if s.get('type') in BASE:
                            cnt[s['type']] += 1
                return cnt
            for label, fs in (('live', live), ('all', flist)):
                cnt = agg(fs)
                n_l = sum(cnt.values()); b = sum(BASE[t] * k for t, k in cnt.items())
                en = byentry.get((tag, nname))
                if label == 'live':
                    all_fleet_stats['fleet_nodes'] += 1
                    if en and en[0] == n_l and n_l > 0:
                        all_fleet_stats['count_match_live'] += 1
                        fval = en[1] / b
                        f_hist[round(fval, 3)] += 1
                        if abs(fval - 1) > 1e-3:
                            f_rows.append((sid, tag, nname, dict(cnt), en, round(b, 3), round(fval, 4)))
                        # non-light ships in those fleets
                        nl = Counter(s.get('type') for f in fs for s in f['ships'] if s.get('type') not in BASE)
                        if nl:
                            nonlight_cases.append((sid, tag, nname, dict(cnt), dict(nl), en))
                    else:
                        unresolved.append((sid, tag, nname, en, n_l, round(b, 3), [(f['name'], 'on_my_way' in f['pm']) for f in flist]))
        for (t, nname), (l, p) in byentry.items():
            if t == tag:
                if TN[nname]['inland']:
                    inland_ent += 1
                if l > maxlight[0]:
                    maxlight = (l, (sid, tag, nname))
        total_entries += sum(1 for (t, _) in byentry if t == tag)
        if sid == 'S79' and tag == 'TUR':
            tur_report = (by_node, byentry, nps, light_mission)

print('\nentries with light_ship (all saves incl. U01/U02):', sum(len(v[2]) for v in per_save.values()))
print('fleet-nodes', all_fleet_stats, 'unresolved', len(unresolved))
print('f histogram (live-fleet count-matched entries):', dict(f_hist), 'total', sum(f_hist.values()))
print('f != 1 rows:')
for r in f_rows:
    print('  ', r)
print('\nUNRESOLVED (entry missing or count differs with on_my_way fleets):')
for u in unresolved:
    print('  ', u)
print('\nnon-light ships inside count-matched fleet groups:')
for n in nonlight_cases:
    print('  ', n)
print('\nmax light_ship in one entry:', maxlight)
print('inland entries', inland_ent, 'inland protect fleets', inland_fleets)
if morales:
    print('light ship morale range on missions', min(morales), max(morales), 'n', len(morales))
print('ships with strength key', strength_ships)

print('\nnps vs node sum vs light ships on missions (S79+S80 only, countries with entries or missions):')
d = [x for x in nps_diff if x[0] in ('S79', 'S80')]
print('country-saves', len(d),
      'nps==missions', sum(1 for s, t, n, ns, lm in d if n == lm),
      'nps==node_sum', sum(1 for s, t, n, ns, lm in d if n == ns))
for x in d:
    if x[2] != x[4] or x[2] != x[3]:
        print('  ', x)

print('\nTUR S79 table:')
by_node, byentry, nps, lm = tur_report
tot = Counter()
for nname, flist in sorted(by_node.items()):
    for f in flist:
        cnt = Counter(s['type'] for s in f['ships'])
        tot.update(cnt)
        base = sum(BASE[t] * k for t, k in cnt.items() if t in BASE)
        print(f"  {f['name']!s:28} node={f['pm']['node']} {nname:14} {dict(cnt)} base={base} on_my_way={f['pm'].get('on_my_way')!r} entry={byentry.get(('TUR', nname))}")
print('  TUR light totals on missions:', {k: v for k, v in tot.items() if k in BASE}, 'nps', nps)
