"""Second pass: f by national idea group, luck=yes and leader maneuver (independent of u345_f_*.py / u345_ships_leader*.py)."""
import sys
sys.path.insert(0, 'scripts/research')
import common, ver2_r11_a as V
from collections import Counter, defaultdict

SAVES = ['S79', 'S80', 'U03', 'U04', 'U05']   # U01/U02 are copies of S80/S79 and are left out

def leader_stats(c):
    out = {}
    def walk(o):
        if isinstance(o, dict):
            if 'maneuver' in o and isinstance(o.get('id'), dict):
                out[o['id']['id']] = o
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(c.get('history'))
    return out

def collect():
    es = {e['id']: e for e in common.entries()}
    rows = []   # one per entry
    for sid in SAVES:
        e = es[sid]
        order, ent = V.entries_with_ships(e)
        cs, fl, allf = V.fleets_of(e, order)
        for key, en in ent.items():
            tag, node = key
            fits = V.fit(en[:2], fl.get(key, []))
            fs = {round(x[2], 4) for x in fits}
            assert len(fs) == 1, (sid, key, fs)
            f = fs.pop()
            # leader status: in which fits does the counted set contain a fleet with a leader?
            lead = [any(fl[key][i]['leader'] for i in x[0]) for x in fits]
            status = 'leader' if all(lead) else ('noleader' if not any(lead) else 'ambiguous')
            man = None
            if status == 'leader':
                ls = leader_stats(cs[tag])
                ms = set()
                for x in fits:
                    for i in x[0]:
                        L = fl[key][i]['leader']
                        if L: ms.add(ls.get(L['id'], {}).get('maneuver'))
                man = sorted(m for m in ms if m is not None)
            groups = cs[tag].get('active_idea_groups')
            rows.append(dict(save=sid, tag=tag, node=node, f=f, status=status, man=man, groups=sorted(groups) if isinstance(groups, dict) else [],
                             luck=cs[tag].get('luck'), n=en[0], sp=en[1]))
    return rows

if __name__ == '__main__':
    rows = collect()
    print('entries', len(rows), 'f histogram', dict(sorted(Counter(r['f'] for r in rows).items())))
    print('per save', {s: len([r for r in rows if r['save'] == s]) for s in SAVES})
    tur = [r for r in rows if r['tag'] == 'TUR']
    print('TUR entries', len(tur), 'f values', Counter(r['f'] for r in tur), {s: len([r for r in tur if r['save'] == s]) for s in SAVES})
    print('status', Counter(r['status'] for r in rows))
    # leader entries
    print('LEADER ENTRIES:')
    for r in rows:
        if r['status'] != 'noleader': print('  ', r['save'], r['tag'], r['node'], 'f', r['f'], r['status'], 'maneuver', r['man'])
    # leaderless pairs (save, country)
    pairs = defaultdict(list)
    for r in rows:
        if r['status'] == 'noleader': pairs[(r['save'], r['tag'])].append(r)
    print('leaderless (save,country) pairs', len(pairs), ' with >1 distinct f:', sum(1 for v in pairs.values() if len({x['f'] for x in v}) > 1))
    nz = {k: v for k, v in pairs.items() if any(x['f'] != 1.0 for x in v)}
    print('pairs with f != 1:', len(nz))
    for k, v in sorted(nz.items()): print('  ', k, sorted({x['f'] for x in v}), [x['node'] for x in v], [g for g in v[0]['groups'] if g.endswith('_ideas')])
    # idea groups vs f over leaderless pairs
    gf = defaultdict(Counter)
    for k, v in pairs.items():
        f = v[0]['f'] if len({x['f'] for x in v}) == 1 else 'mixed'
        for g in v[0]['groups']: gf[g][f] += 1
    print('idea groups that occur in any f != 1 pair:')
    for g, c in sorted(gf.items()):
        if any(f != 1.0 for f in c): print('  ', g, dict(c))
    print('f=1 pairs carrying fijian/luzon/samoan:', sum(c[1.0] for g, c in gf.items() if g in ('fijian_ideas', 'luzon_ideas', 'samoan_ideas')))
    # all f != 1 pairs covered?
    three = {'fijian_ideas', 'luzon_ideas', 'samoan_ideas'}
    print('f!=1 pairs without any of the three groups:', [k for k, v in nz.items() if not (set(v[0]['groups']) & three)])
    # luck crosstab
    ct = Counter((bool(v[0]['luck']), v[0]['f'] != 1.0) for v in pairs.values())
    print('luck crosstab (lucky, f!=1):', dict(ct))
    print('lucky tags', sorted({(s, t) for (s, t), v in pairs.items() if v[0]['luck']})[:40])
    # national groups in f=1 pairs: list of groups seen with f == 1 that end with _ideas and appear in <=3 tags overall
    tagsets = defaultdict(set)
    for (s, t), v in pairs.items():
        for g in v[0]['groups']: tagsets[g].add(t)
    rare = sorted((g, len(ts)) for g, ts in tagsets.items() if len(ts) <= 3)
    print('groups seen in <=3 countries (national-type):', len(rare))
    print('  of which in f=1 pairs only:', sum(1 for g, _ in rare if g not in three and all(f == 1.0 for f in gf[g])))
    print('  defensive_ideas:', dict(gf['defensive_ideas']))
    for g in ('hawaiian_ideas', 'chinese_ideas', 'swahili_ideas', 'maori_ideas'): print('  ', g, dict(gf[g]))
