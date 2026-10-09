"""Venice series: is `prev` computed with the link weights of the PREVIOUS tick? Compare per tick save: gate with current weights, with previous-tick weights, no gate."""
import sys
sys.path.insert(0, "scripts/research")
import venice_load as V, venice_a_prev as A
from final_r12_common import OUT, lst, entries_of

def state(p):
    ns = {n['definitions']: n for n in V.nodes(p)}
    return ns, {k: entries_of(n) for k, n in ns.items()}, {k: [float(x) for x in lst(n.get('steer_power'))] for k, n in ns.items()}

def test(cur, prevw):
    ns, ent, w_cur = cur
    r = dict(cand=0, cur=0, lag=0, plain=0, lag_only_fail=[])
    for B, tg in ent.items():
        for tag, c in tg.items():
            if 'max_pow' not in c: continue
            r['cand'] += 1
            pl = cu = lg = 0.0
            for i, D_ in enumerate(OUT.get(B, [])):
                d = ent.get(D_, {}).get(tag)
                if not d or d.get('province_power', 0) < 10: continue
                v = A.d5(d['province_power']); pl += v
                if i < len(w_cur[B]) and w_cur[B][i] > 0: cu += v
                if i < len(prevw[B]) and prevw[B][i] > 0: lg += v
            rec = c.get('prev', 0.0)
            ok = lambda x: abs(x - rec) < 5e-4
            r['plain'] += ok(pl); r['cur'] += ok(cu); r['lag'] += ok(lg)
            if not ok(lg): r['lag_only_fail'].append((B, tag, rec, round(lg, 3), round(pl, 3)))
    return r

if __name__ == '__main__':
    fs = V.files(); st = {p.stem[6:]: state(p) for p in fs}
    names = list(st)
    pairs = [('1444_11_30', '1444_12_01'), ('1444_12_31', '1445_01_01'), ('1445_01_31', '1445_02_01'), ('1445_02_28', '1445_03_01'), ('1445_03_31', '1445_04_01'), ('1445_04_01', '1445_05_01'), ('1445_05_01', '1445_06_01'), ('1445_06_01', '1445_07_02'), ('1444_11_11', '1444_11_30')]
    for a, b in pairs:
        r = test(st[b], st[a][2])
        print(f"{a} -> {b}: candidates {r['cand']}  plain {r['plain']}  current-weight gate {r['cur']}  previous-save-weight gate {r['lag']}  lag misses {r['lag_only_fail'][:4]}")

def ever_positive(states):
    out = {}
    for ns, ent, w in states:
        for k, v in w.items():
            cur = out.setdefault(k, [0.0] * len(v))
            for i, x in enumerate(v):
                if i < len(cur): cur[i] = max(cur[i], x)
    return out

def main2():
    fs = V.files(); names = [p.stem[6:] for p in fs]; st = [state(p) for p in fs]
    ticks = ['1444_12_01', '1445_01_01', '1445_02_01', '1445_03_01', '1445_04_01', '1445_05_01', '1445_06_01', '1445_07_02']
    for t in ticks:
        i = names.index(t)
        before = st[:i]                      # all saves before this tick save
        r_start = test(st[i], st[0][2])     # weights of the first save (bookmark start)
        r_ever = test(st[i], ever_positive(before))
        r_prev = test(st[i], st[i - 1][2])
        print(f"{t}: cand {r_ever['cand']} start-weights gate {r_start['lag']} ever-positive-before gate {r_ever['lag']} previous-save gate {r_prev['lag']} misses(ever) {r_ever['lag_only_fail'][:3]}")

if __name__ == '__main__':
    main2()
