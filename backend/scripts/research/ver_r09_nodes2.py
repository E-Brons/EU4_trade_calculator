"""Independent verification (R09 response_1), second pass: max, pull_power, top_power, prev variants, stubs."""
import sys, re, math, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
def t3(x): return math.floor(x * 1000 + 1e-7) / 1000
def ents(n): return {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}
C = collections.Counter(); F = collections.defaultdict(list)
for e in common.entries():
    sid = e['id']; ns = common.nodes(e); order = [n['definitions'] for n in ns]; byid = {n['definitions']: n for n in ns}
    down = collections.defaultdict(set)
    for n in ns:
        inc = n.get('incoming', [])
        inc = inc if isinstance(inc, list) else [inc]
        for i in inc: down[order[int(i['from']) - 1]].add(n['definitions'])
    cache = {}
    def reach(x):
        if x in cache: return cache[x]
        seen, st = set(), [x]
        while st:
            y = st.pop()
            for z in down.get(y, ()):
                if z not in seen: seen.add(z); st.append(z)
        cache[x] = seen; return seen
    coll = collections.defaultdict(set)
    for n in ns:
        for t, v in ents(n).items():
            if 'total' in v: coll[t].add(n['definitions'])
    for n in ns:
        nid = n['definitions']; es = ents(n)
        # stubs without max_demand
        for t, v in es.items():
            if 'max_demand' not in v:
                C['no_md'] += 1; C['no_md_only_potential'] += set(v) == {'potential'}
        # max variants
        if 'max' in n and 'p_pow' in n:
            sp = sum(v.get('province_power', 0) for v in es.values())
            A = sum(v['max_pow'] - v.get('prev', 0) for v in es.values() if 'max_pow' in v)          # max = sum(max_pow - prev)
            B = n['p_pow'] + sum(v['max_pow'] - v.get('prev', 0) - v.get('province_power', 0) for v in es.values() if 'max_pow' in v)  # p_pow + sum(ship+extras)
            Cc = n['p_pow'] + sum(v['max_pow'] - v.get('prev', 0) for v in es.values() if 'max_pow' in v)  # as literally written in the response
            for nm, x in (('A sum(max_pow-prev)', A), ('B p_pow+sum(max_pow-prev-province_power)', B), ('C p_pow+sum(max_pow-prev) [as written]', Cc)):
                if abs(x - n['max']) <= 0.0025: C['max ' + nm] += 1
            C['max_nodes'] += 1
            if abs(B - n['max']) > 0.0025: F['maxB'].append((sid, nid, n['max'], round(B, 3)))
            if abs(A - n['max']) > 0.0025: F['maxA'].append((sid, nid, n['max'], round(A, 3), round(n['p_pow'], 3), round(sp, 3)))
        # pull
        if 'pull_power' in n:
            C['pull_nodes'] += 1; dn = reach(nid); s = 0.0
            for t, v in es.items():
                steer = 'type' in v
                cd = 'total' not in v and bool(coll.get(t, set()) & dn)
                if steer or cd: s += v.get('val', 0) - v.get('t_out', 0) + v.get('t_in', 0)
            if abs(s - n['pull_power']) <= 0.0025: C['pull_ok'] += 1
            else: F['pull'].append((sid, nid, round(s, 3), n['pull_power']))
        # top_power
        if 'top_power' in n:
            C['tp_nodes'] += 1
            eff = {t: v.get('val', 0) - v.get('t_out', 0) + v.get('t_in', 0) for t, v in es.items()}
            pos = sorted(((x, t) for t, x in eff.items() if x > 0), reverse=True)
            ok = set(n['top_power']) == {t for _, t in pos} and all(abs(a - b) <= 0.0015 for a, b in zip(n['top_power_values'], [x for x, _ in pos])) and len(n['top_power_values']) == len(pos)
            C['tp_ok'] += ok
            if not ok: F['tp'].append((sid, nid))
        # prev variants
        for t, v in es.items():
            if 'max_pow' in v or 'prev' in v:
                C['prev_entries'] += 1
                pvs = [ents(byid[d]).get(t, {}).get('province_power', 0.0) for d in down.get(nid, ())]
                r_sum_then_trunc = t3(sum(p / 5 for p in pvs if p >= 10))
                r_plain = t3(sum(p / 5 for p in pvs))
                r_perlink = sum(t3(p / 5) for p in pvs if p >= 10)
                got = v.get('prev', 0.0)
                C['prev thresh sum-then-trunc tol0.0015'] += abs(r_sum_then_trunc - got) <= 0.0015
                C['prev thresh per-link tol0.0015'] += abs(r_perlink - got) <= 0.0015
                C['prev plain sum/5 tol0.0015'] += abs(r_plain - got) <= 0.0015
                C['prev thresh > (not >=)'] += abs(t3(sum(p / 5 for p in pvs if p > 10)) - got) <= 0.0015
                if abs(r_sum_then_trunc - got) > 0.0015: F['prev'].append((sid, nid, t, got, r_sum_then_trunc))
for k in sorted(C): print(k, C[k])
for k, v in F.items(): print('FAIL', k, len(v), collections.Counter(x[0] for x in v).most_common(6), v[:5])
pf = F['prev']; print('prev fails by (node,tag):', collections.Counter((x[1], x[2]) for x in pf).most_common(12))
print('MOR fails', sorted((x[0], x[1], x[3], x[4], round(x[3] - x[4], 3)) for x in F['prev'] if x[2] == 'MOR'))
