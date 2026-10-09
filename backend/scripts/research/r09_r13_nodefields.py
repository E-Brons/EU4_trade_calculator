"""R09 Q2: test hypotheses for node-level fields p_pow, max, highest_power, collector_power, total, top_*, over all saves."""
import sys, re, collections, math
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')

def ents(n):
    return {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}

def close(a, b, tol=0.0015):
    return abs(a - b) <= tol

stats = collections.defaultdict(lambda: [0, 0])
fails = collections.defaultdict(list)
def chk(name, ok, ctx):
    stats[name][0] += 1
    if not ok:
        stats[name][1] += 1
        if len(fails[name]) < 4: fails[name].append(ctx)

for e in common.entries():
    for n in common.nodes(e):
        if 'p_pow' not in n: continue
        es = ents(n); nid = n['definitions']; ctx = (e['id'], nid)
        pp = n['p_pow']; mx = n['max']
        sp = sum(v.get('province_power', 0) for v in es.values())
        ship = sum(v.get('ship_power', 0) for v in es.values())
        chk('p_pow=sum(province_power)', close(pp, sp, 0.01 * max(1, len(es))*0.001+0.005), ctx + (pp, sp))
        chk('p_pow=sum(province_power) tol0.01', close(pp, sp, 0.01), ctx + (pp, sp))
        chk('max-p_pow==20', close(mx - pp, 20, 0.01), ctx + (mx - pp,))
        # alt: max - p_pow vs ship power
        chk('max-p_pow==ship_power', close(mx - pp, ship, 0.01), ctx + (mx - pp, ship))
        chk('max-p_pow==ship_power+20', close(mx - pp, ship + 20, 0.01), ctx + (mx - pp, ship))
        # highest_power
        hp = n['highest_power']
        provs = sorted((v.get('province_power', 0) for v in es.values()), reverse=True)
        chk('highest_power=max province_power', close(hp, provs[0], 0.01), ctx + (hp, provs[0]))
        vals = sorted((v.get('val', 0) for v in es.values()), reverse=True)
        chk('highest_power=max val', close(hp, vals[0], 0.01), ctx + (hp, vals[0]))
        mp = sorted((v.get('max_pow', 0) for v in es.values()), reverse=True)
        chk('highest_power=max max_pow', close(hp, mp[0], 0.01), ctx + (hp, mp[0]))
        # total
        tot = n.get('total')
        if tot is not None:
            chk('total=sum val', close(tot, sum(v.get('val', 0) for v in es.values()), 0.01 * 1), ctx + (tot, sum(v.get('val', 0) for v in es.values())))
        # collector_power
        cp = n.get('collector_power')
        if cp is not None:
            chk('collector_power=retain_power', close(cp, n.get('retain_power', -1), 0.0015), ctx)
            coll = sum(v['val'] - v.get('t_out', 0) + v.get('t_in', 0) for v in es.values() if 'total' in v)
            chk('collector_power=sum(val-tout+tin collectors)', close(cp, coll, 0.01), ctx + (cp, coll))
            chk('collector_power_incl==collector_power', close(n['collector_power_including_pirates'], cp, 0.0015), ctx + (cp, n['collector_power_including_pirates']))
        # top_power
        tp, tv = n.get('top_power'), n.get('top_power_values')
        if tp is not None:
            tp = tp if isinstance(tp, list) else [tp]; tv = tv if isinstance(tv, list) else [tv]
            chk('top_power sorted desc', all(tv[i] >= tv[i+1] for i in range(len(tv)-1)), ctx)
            chk('top_power_values = val of tag', all(close(tv[i], es.get(t, {}).get('val', -1), 0.0015) for i, t in enumerate(tp)), ctx + (list(zip(tp, tv))[:3],))
            chk('top_power_values = max_pow of tag', all(close(tv[i], es.get(t, {}).get('max_pow', -1), 0.0015) for i, t in enumerate(tp)), ctx)
            chk('top_power_values = province_power of tag', all(close(tv[i], es.get(t, {}).get('province_power', -1), 0.0015) for i, t in enumerate(tp)), ctx)
            chk('top_power_values = max_pow*? (val/max_pow ratio)', True, ctx)
        tpr, tpv = n.get('top_provinces'), n.get('top_provinces_values')
        if tpr is not None:
            tpr = tpr if isinstance(tpr, list) else [tpr]; tpv = tpv if isinstance(tpv, list) else [tpv]
            chk('top_provinces_values=province_power of tag', all(close(tpv[i], es.get(t, {}).get('province_power', -1), 0.0015) for i, t in enumerate(tpr)), ctx + (list(zip(tpr, tpv))[:3],))
            chk('top_provinces sorted desc', all(tpv[i] >= tpv[i+1] for i in range(len(tpv)-1)), ctx)
for k, (t, f) in stats.items():
    print(f'{k:60s} n={t:6d} fail={f:6d}')
    for c in fails[k][:3]: print('     ', c)
