"""Venice series: zero-weight links with downstream province_power >= 10 - which ones contribute to `prev` (plain contribution counted) and what distinguishes them."""
import sys, collections
sys.path.insert(0, "scripts/research")
import venice_load as V, venice_a_prev as A
from final_r12_common import OUT, lst, entries_of

def rows(p):
    ns = {n['definitions']: n for n in V.nodes(p)}; ent = {k: entries_of(n) for k, n in ns.items()}
    order = [n['definitions'] for n in V.nodes(p)]
    out = []
    for B, tg in ent.items():
        w = [float(x) for x in lst(ns[B].get('steer_power'))]
        for tag, c in tg.items():
            if 'max_pow' not in c: continue
            contrib = {D: A.d5(ent[D][tag]['province_power']) for D in OUT.get(B, []) if ent.get(D, {}).get(tag, {}).get('province_power', 0) >= 10}
            zero = [D for i, D in enumerate(OUT.get(B, [])) if D in contrib and i < len(w) and w[i] == 0]
            if not zero: continue
            rec = c.get('prev', 0.0)
            gated = sum(v for i, (D, v) in enumerate([(D, contrib[D]) for D in OUT[B] if D in contrib]) if True) - sum(contrib[D] for D in zero)
            plain = sum(contrib.values())
            kind = 'plain' if abs(rec - plain) < 5e-4 else ('gated' if abs(rec - gated) < 5e-4 else 'other')
            # does downstream node have an incoming entry from B with value>0 ?
            inc = {}
            for D in zero:
                for i in lst(ns[D].get('incoming')):
                    if isinstance(i, dict) and order[int(i['from']) - 1] == B: inc[D] = i.get('value', 0)
            out.append(dict(B=B, tag=tag, zero=zero, kind=kind, w=w, rec=rec, plain=round(plain, 3), inc=inc, steers=('type' in c), coll=('total' in c or bool(c.get('has_capital')))))
    return out

if __name__ == '__main__':
    for stem in ['1444_11_11', '1444_12_01', '1445_01_01', '1445_07_02']:
        p = [x for x in V.files() if x.stem.endswith(stem)][0]
        r = rows(p)
        print(stem, collections.Counter(x['kind'] for x in r))
        for x in r:
            if x['kind'] != 'plain': print('   ', x['kind'], x['B'], x['tag'], x['zero'], x['w'], 'rec', x['rec'], 'plain', x['plain'], 'inc', x['inc'])
        c = collections.Counter((x['kind'], bool(x['inc']), x['steers'], x['coll']) for x in r)
        print('   (kind, incoming entry exists, tag steers at B, tag collects at B):', dict(c))
