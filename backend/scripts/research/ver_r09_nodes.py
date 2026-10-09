"""Independent verification (R09 response_1): trade-node claims. Does not reuse the author's r09_r13_* logic."""
import sys, re, math, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
PLAYED = {'S79', 'S80', 'U01', 'U02'}
def t3(x): return math.floor(x * 1000 + 1e-7) / 1000
def ents(n): return {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}

C = collections.Counter(); fails = collections.defaultdict(list)
for e in common.entries():
    sid = e['id']; ns = common.nodes(e); C['saves'] += 1
    order = [n['definitions'] for n in ns]
    down = collections.defaultdict(set)      # upstream -> downstream, derived from incoming.from (1-based)
    for n in ns:
        for i in n.get('incoming', []) if isinstance(n.get('incoming'), list) else ([n['incoming']] if 'incoming' in n else []):
            down[order[int(i['from']) - 1]].add(n['definitions'])
    byid = {n['definitions']: n for n in ns}
    # reachability downstream
    def reach(x, memo={}):
        seen, st = set(), [x]
        while st:
            y = st.pop()
            for z in down.get(y, ()):
                if z not in seen: seen.add(z); st.append(z)
        return seen
    collects_in = collections.defaultdict(set)   # tag -> nodes where it has 'total'
    for n in ns:
        for t, v in ents(n).items():
            if 'total' in v: collects_in[t].add(n['definitions'])
    C['nodes'] += len(ns)
    for n in ns:
        nid = n['definitions']; es = ents(n)
        C['entries'] += len(es)
        C['entries_only_max_demand'] += sum(1 for v in es.values() if set(v) == {'max_demand'})
        rp = n.get('retain_power')
        # C-01 power_fraction / money / total set equality
        a = {t for t, v in es.items() if 'power_fraction' in v}; b = {t for t, v in es.items() if 'total' in v}; c = {t for t, v in es.items() if 'money' in v}
        C['nodes_pf==total==money'] += (a == b == c)
        for t in a:
            v = es[t]; eff = v['val'] - v.get('t_out', 0) + v.get('t_in', 0)
            C['pf_entries'] += 1
            d = abs(t3(eff / rp) - v['power_fraction']) if rp else 9
            if d > 0.0005: C['pf_fail_strict'] += 1; fails['pf'].append((sid, nid, t, v['power_fraction'], round(eff, 3), rp))
            if d > 0.0015: C['pf_fail_loose'] += 1
        # C-02 potential
        for t, v in es.items():
            if 't_in' in v or 't_out' in v:
                C['transfer_entries'] += 1
                if n.get('total') and abs(t3((v.get('t_out', 0) - v.get('t_in', 0)) / n['total']) - v.get('potential', 9)) <= 0.0005 + 1e-9: C['potential_ok'] += 1
                else:
                    # truncation toward zero for negatives
                    q = (v.get('t_out', 0) - v.get('t_in', 0)) / n['total'] if n.get('total') else 0
                    if abs(math.trunc(q * 1000 + (1e-7 if q >= 0 else -1e-7)) / 1000 - v.get('potential', 9)) <= 0.0005: C['potential_ok_trunc0'] += 1
                    else: fails['potential'].append((sid, nid, t))
            elif 'potential' in v:
                C['potential_no_transfer'] += 1; C['potential_no_transfer_' + nid + ('_' + str(v['potential']) if t != 'PIR' else '_PIR' + str(v['potential']))] += 1
        # C-03 pull_power via own rule
        if 'pull_power' in n:
            C['pull_nodes'] += 1
            dn = reach(nid); s = 0.0
            for t, v in es.items():
                if 'val' not in v: continue
                steer = ('type' in v)
                collect_down = (t in collects_in and 'total' not in v and bool(collects_in[t] & dn))
                if steer or collect_down or ('val' in v and 'total' not in v and not v.get('has_trader') and False):
                    s += v['val'] - v.get('t_out', 0) + v.get('t_in', 0)
                elif ('total' not in v) and (v.get('t_in') or v.get('t_out')) and bool(collects_in.get(t, set()) & dn):
                    s += v['val'] - v.get('t_out', 0) + v.get('t_in', 0)
            if abs(s - n['pull_power']) <= 0.0025: C['pull_ok'] += 1
            else: fails['pull'].append((sid, nid, round(s, 3), n['pull_power']))
        # C-04 max_demand
        for t, v in es.items():
            if 'max_demand' in v:
                C['md_n'] += 1; m = v['max_demand']; C['md_lt1'] += m < 1.0; C['md_gt2'] += m > 2.0; C['md_eq1'] += m == 1.0
                C['md_min'] = min(C.get('md_min', 9) or 9, m) if 'md_min' in C else m
                C['md_max'] = max(C.get('md_max', 0), m)
            if 'val' in v and 'max_pow' in v and 'max_demand' in v:
                C['val_triples'] += 1
                if abs(t3(v['max_pow'] * v['max_demand']) - v['val']) <= 0.0005 + 1e-9: C['val_ok'] += 1
                else: fails['val'].append((sid, nid, t, v['val'], v['max_pow'], v['max_demand']))
        # C-05
        if 'num_collectors' in n:
            C['nc_nodes'] += 1
            C['ncp=nc+1'] += n['num_collectors_including_pirates'] == n['num_collectors'] + 1
            C['PIR_md1_only'] += ('PIR' in es and es['PIR'] == {'max_demand': 1.0})
            C['cpp==cp'] += abs(n['collector_power_including_pirates'] - n['collector_power']) <= 0.0015
            k = sum(1 for v in es.values() if 'total' in v)
            if k == n['num_collectors']: C['nc==#total'] += 1
            else: fails['nc'].append((sid, nid, n['num_collectors'], k))
            # C-09
            if abs(n['collector_power'] - n['retain_power']) <= 0.0015: C['cp==retain'] += 1
            else: fails['cp'].append((sid, nid, n['collector_power'], n['retain_power']))
        # C-11 top_power
        if 'top_power' in n:
            C['toppow_nodes'] += 1
            eff = {t: v['val'] - v.get('t_out', 0) + v.get('t_in', 0) for t, v in es.items() if 'val' in v}
            pos = sorted([(x, t) for t, x in eff.items() if x > 0], reverse=True)
            ok = (set(n['top_power']) == {t for _, t in pos}) and len(n['top_power']) == len(n['top_power_values']) and all(abs(a - b) <= 0.0015 for a, b in zip(sorted(n['top_power_values'], reverse=True), [x for x, _ in pos])) and n['top_power_values'] == sorted(n['top_power_values'], reverse=True)
            C['toppow_ok'] += ok
            if not ok: fails['toppow'].append((sid, nid))
            C['toppow_maxlen'] = max(C.get('toppow_maxlen', 0), len(n['top_power']))
        # C-12 top_provinces
        pp = {t: v.get('province_power', 0) for t, v in es.items() if v.get('province_power', 0) > 0}
        if 'top_provinces' in n:
            C['topprov_nodes'] += 1
            ok = set(n['top_provinces']) == set(pp) and all(abs(pp[t] - x) <= 0.0015 for t, x in zip(n['top_provinces'], n['top_provinces_values'])) and n['top_provinces_values'] == sorted(n['top_provinces_values'], reverse=True)
            C['topprov_ok'] += ok
            if not ok: fails['topprov'].append((sid, nid))
            C['topprov_maxlen'] = max(C.get('topprov_maxlen', 0), len(n['top_provinces']))
        else:
            if 'top_power' in n and not pp: C['topprov_absent_and_no_pp'] += 1
            elif 'top_power' in n: C['topprov_absent_but_pp'] += 1
        # C-07 max
        if 'max' in n and 'p_pow' in n:
            C['max_nodes'] += 1
            s = sum(v['max_pow'] - v.get('prev', 0) for v in es.values() if 'max_pow' in v)
            if abs(n['p_pow'] + s - n['max']) <= 0.0025: C['max_ok'] += 1
            else: fails['max'].append((sid, nid, n['max'], round(n['p_pow'] + s, 3)))
        # C-10 total
        if 'total' in n:
            sv = sum(v.get('val', 0) for v in es.values())
            d = n['total'] - sv
            C['total_nodes'] += 1
            if d > 0.01: C['total_gt_sum_0.01'] += 1
            if d < -0.01: C['total_lt_sum'] += 1
        # C-15
        C['tsp_1.1.1'] += n.get('most_recent_treasure_ship_passage') == '1.1.1'
        # C-16 prev (one hop, direct downstream, from incoming graph)
        for t, v in es.items():
            if 'max_pow' in v or 'prev' in v:
                C['prev_entries'] += 1; s = 0.0
                for d_ in down.get(nid, ()):
                    pv = ents(byid[d_]).get(t, {}).get('province_power', 0.0)
                    if pv >= 10: s += t3(pv / 5)
                if abs(s - v.get('prev', 0.0)) <= 0.0025: C['prev_ok'] += 1
                else: fails['prev'].append((sid, nid, t, v.get('prev', 0.0), round(s, 3)))
            # C-17 extras
            if 'max_pow' in v:
                x = round(v['max_pow'] - v.get('province_power', 0) - v.get('ship_power', 0) - v.get('prev', 0), 3)
                C['extras:' + str(x)] += 1
for k in sorted(C, key=str):
    if not k.startswith('potential_no_transfer_') and not k.startswith('extras:'): print(k, C[k])
print('potential_no_transfer breakdown', {k[len('potential_no_transfer_'):]: v for k, v in C.items() if k.startswith('potential_no_transfer_')})
ex = sorted(((float(k[7:]), v) for k, v in C.items() if k.startswith('extras:')), key=lambda x: -x[1])
print('extras', ex[:16], 'outside {0,5}:', sum(v for x, v in ex if x not in (0.0, 5.0)))
for k, v in fails.items(): print('FAIL', k, len(v), collections.Counter(x[0] for x in v).most_common(5), v[:4])
