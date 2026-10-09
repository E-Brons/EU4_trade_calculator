"""Verifier (independent): R10 gap = total - sum(val) vs power of provinces not credited to any entry."""
import sys, re, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
C = collections.Counter(); resid = []; only = []
for e in common.entries():
    ns = common.nodes(e)
    ps = common.block(e, 'provinces')
    bynode = collections.defaultdict(list)
    for k, p in ps.items():
        if isinstance(p, dict) and 'trade' in p:
            bynode[p['trade']].append(p)
    for n in ns:
        nid = n['definitions']
        ents = {t: v for t, v in n.items() if TAG.match(t) and isinstance(v, dict)}
        if 'total' not in n:
            C['no total'] += 1; continue
        C['nodes with total'] += 1
        C['total but no p_pow'] += 'p_pow' not in n
        sval = sum(v.get('val', 0.0) for v in ents.values())
        gap = n['total'] - sval
        provsum = sum(p.get('trade_power', 0.0) for p in bynode[nid])
        C['p_pow == sum province trade_power (0.002)'] += abs(provsum - n.get('p_pow', 0.0)) <= 0.002
        credited = sum(v.get('province_power', 0.0) for v in ents.values())
        uncred = n.get('p_pow', 0.0) - credited
        reb = sum(p.get('trade_power', 0.0) for p in bynode[nid] if (p.get('controller') or 'NONE') in ('REB', 'NONE') or p.get('controller') not in ents)
        if gap > 0.0035:
            C['gap>0.0035'] += 1
            if abs(gap - reb) <= 0.0035: C['gap==REB/uncontrolled power (0.0035)'] += 1
            elif abs(gap - uncred) <= 0.0035:
                C['gap==p_pow-credited only'] += 1; only.append((e['id'], nid, round(gap,3), round(reb,3)))
            else:
                C['gap unexplained'] += 1; resid.append((e['id'], nid, round(gap, 3), round(reb, 3), round(uncred, 3)))
        else:
            C['gap<=0.0035'] += 1
            if abs(uncred) > 0.0035: C['no gap but p_pow != credited'] += 1
        if gap > 0.01: C['gap>0.01'] += 1
        if gap > 0.02 * n['total']: C['gap>2%'] += 1
        if gap < -0.01: C['gap<-0.01'] += 1
for k, v in C.items(): print(v, k)
print(len(resid), resid[:10])
print('p_pow-credited-only:', only)
print('unexplained by save', collections.Counter(r[0] for r in resid))
