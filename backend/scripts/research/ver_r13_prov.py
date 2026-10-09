"""Independent verification (R09 C-06/C-08/C-10, R13 C-02): province sums vs node/entry fields."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
PLAYED = {'S79', 'S80', 'U01', 'U02'}
C = collections.Counter(); F = collections.defaultdict(list)
for e in common.entries():
    sid = e['id']; ns = common.nodes(e); pr = common.block(e, 'provinces')
    by_node = collections.defaultdict(list)
    for pid, p in pr.items():
        if isinstance(p, dict) and p.get('trade') and isinstance(p.get('trade_power'), (int, float)):
            by_node[p['trade']].append((pid, p))
    for n in ns:
        nid = n['definitions']; provs = by_node.get(nid, [])
        es = {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}
        tot = sum(p['trade_power'] for _, p in provs); tol = 0.0005 * max(1, len(provs)) + 0.0005
        reb = sum(p['trade_power'] for _, p in provs if p.get('controller') == 'REB')
        entry_sum = sum(v.get('province_power', 0) for v in es.values())
        if 'p_pow' in n:
            C['p_pow_nodes'] += 1
            ok = abs(n['p_pow'] - tot) <= tol
            C['p_pow==sum(all provinces)'] += ok
            if not ok: F['p_pow'].append((sid, nid, n['p_pow'], round(tot, 3)))
            exceeds = n['p_pow'] - entry_sum > 0.0005 * max(1, len(es)) + 0.0005
            has_reb = reb > 0
            C['p_pow>entry_sum'] += exceeds; C['has_rebel_power'] += has_reb; C['both'] += exceeds and has_reb
            if exceeds and has_reb and not ok: C['rebel_nodes_in_p_pow_fail'] += 1
            # rebel explained total gap
            if 'total' in n:
                sv = sum(v.get('val', 0) for v in es.values()); gap = n['total'] - sv
                if gap > 0.01:
                    C['gap>0.01'] += 1
                    if abs(gap - reb) <= 0.0035: C['gap==rebel_power'] += 1
        if 'highest_power' in n and provs:
            C['hp_nodes'] += 1
            mx = max(p['trade_power'] for _, p in provs)
            if abs(mx - n['highest_power']) <= 0.0015: C['hp_ok'] += 1
            else: F['hp'].append((sid, nid, n['highest_power'], mx))
        # province_power per (node, controller)
        ctrl = collections.defaultdict(float); own = collections.defaultdict(float); cnt = collections.Counter()
        for pid, p in provs:
            if p.get('controller'): ctrl[p['controller']] += p['trade_power']; cnt[p['controller']] += 1
            if p.get('owner'): own[p['owner']] += p['trade_power']
        tags = set(es) | {t for t in ctrl if t != 'REB'}
        for t in tags:
            pp = es.get(t, {}).get('province_power', 0.0); s = ctrl.get(t, 0.0)
            if pp <= 0 and s <= 0: continue
            C['pairs'] += 1
            tl = 0.0005 * max(1, cnt.get(t, 0)) + 0.0005
            if abs(pp - s) > tl:
                C['ctrl_fail'] += 1; F['ctrl'].append((sid, nid, t, pp, round(s, 3)))
            if abs(pp - own.get(t, 0.0)) > tl: C['owner_fail'] += 1
    # occupation
    for nid, provs in by_node.items():
        ne = {k: v for k, v in next(n for n in ns if n['definitions'] == nid).items() if TAG.match(k) and isinstance(v, dict)}
        # occupied provinces: controller != owner, controller != REB, trade_power>0
    # occupied province check per save
    nodemap = {n['definitions']: n for n in ns}
    ctrl_sum = collections.defaultdict(float); own_sum = collections.defaultdict(float)
    for nid, provs in by_node.items():
        for pid, p in provs:
            if p.get('controller'): ctrl_sum[(nid, p['controller'])] += p['trade_power']
            if p.get('owner'): own_sum[(nid, p['owner'])] += p['trade_power']
    for nid, provs in by_node.items():
        if nid not in nodemap: continue
        for pid, p in provs:
            o, c = p.get('owner'), p.get('controller')
            if o and c and o != c and c != 'REB' and p['trade_power'] > 0:
                C['occupied'] += 1
                ent = lambda t: nodemap[nid].get(t, {}).get('province_power', 0.0) if isinstance(nodemap[nid].get(t), dict) else 0.0
                C['occ_owner_entry==owner_sum_incl'] += abs(ent(o) - own_sum[(nid, o)]) <= 0.0015 and own_sum[(nid, o)] != ctrl_sum[(nid, o)]
                okc = abs(ent(c) - ctrl_sum[(nid, c)]) <= 0.0005 * 5 + 0.0005
                C['occ_ctrl_entry==ctrl_sum'] += okc
                if sid in PLAYED: C['occ_played'] += 1; C['occ_played_ok'] += okc
                else: C['occ_start'] += 1; C['occ_start_ok'] += okc
for k in sorted(C): print(k, C[k])
for k, v in F.items(): print('FAIL', k, len(v), collections.Counter(x[0] for x in v).most_common(8), v[:4])
f = F['ctrl']; print('ctrl fails in played', sum(1 for x in f if x[0] in PLAYED), 'start', sum(1 for x in f if x[0] not in PLAYED)); print([x for x in f if x[0] not in PLAYED][:20])
pf = F['p_pow']; print('p_pow fails played', sum(1 for x in pf if x[0] in PLAYED), 'start', [(x[0], x[1], round(x[2] - x[3], 2)) for x in pf if x[0] not in PLAYED])
hp = F['hp']; print('hp fails played', sum(1 for x in hp if x[0] in PLAYED), 'of', len(hp))
