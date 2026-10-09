"""Second-pass, independent re-computation of the headline identities of the 2026-10-05 updates (R04/R05/R08/R09/R10/R12).
Own parsing of the cached trade trees (common.nodes), own counting; graph = data/tradenodes.json. Run from backend/.
Usage: ver2_c_identities.py [ids,comma]  -> per-save counters + group totals (start saves / played saves)."""
import json, re, sys, collections
from decimal import Decimal, ROUND_DOWN
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common

TAG = re.compile(r'^[A-Z0-9]{2,4}$')
G = json.load(open('data/tradenodes.json'))['nodes']
OUT = {n: [o['target'] for o in v['outgoing']] for n, v in G.items()}

def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def tr3(a, mul=None, div=None):               # truncate to 3 decimals (toward zero) in exact decimal arithmetic
    d = Decimal(repr(float(a)))
    if mul is not None: d = d * Decimal(repr(float(mul)))
    if div is not None: d = d / Decimal(repr(float(div)))
    return float(d.quantize(Decimal('0.001'), rounding=ROUND_DOWN))

def lst(v):
    if v is None: return []
    return v if isinstance(v, list) else [v]

def entries_of(n):
    return {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}

def is_entry(c):
    return bool(set(c) - {'max_demand'})

def run(e):
    nl = common.nodes(e); order = [n['definitions'] for n in nl]; ns = {n['definitions']: n for n in nl}
    E = {nid: entries_of(n) for nid, n in ns.items()}
    c = collections.Counter(); ex = collections.defaultdict(list)
    # incoming per (from,to)
    inc = {}
    for to, n in ns.items():
        for i in lst(n.get('incoming')):
            if isinstance(i, dict):
                inc.setdefault((order[int(i['from']) - 1], to), []).append((num(i.get('value')) or 0.0, num(i.get('add')) or 0.0))
    in_sum = collections.defaultdict(float)
    for (b, to), L in inc.items():
        in_sum[to] += sum(v for v, a in L)
    for nid, n in ns.items():
        ents = E[nid]
        # val identity
        for tag, x in ents.items():
            if all(k in x for k in ('val', 'max_pow', 'max_demand')):
                c['val n'] += 1
                c['val ok'] += abs(tr3(x['max_pow'], mul=x['max_demand']) - num(x['val'])) <= 0.0005 + 1e-9
        # top_power_values = val - t_out + t_in
        for tag, v in zip(lst(n.get('top_power')), lst(n.get('top_power_values'))):
            x = ents.get(tag)
            if x and 'val' in x:
                c['tpv n'] += 1
                ok = abs((num(x['val']) - (num(x.get('t_out')) or 0.0) + (num(x.get('t_in')) or 0.0)) - num(v)) <= 0.0015
                c['tpv ok'] += ok
                if not ok and len(ex['tpv']) < 3: ex['tpv'].append((nid, tag, v))
            elif x is None:
                c['tpv tag without entry'] += 1; ex['tpv noentry'].append((nid, tag, v)) if len(ex['tpv noentry']) < 4 else None
        # max = p_pow + sum(max_pow - prev - province_power)
        if 'max' in n and 'p_pow' in n:
            s = sum((num(x['max_pow']) - (num(x.get('prev')) or 0.0) - (num(x.get('province_power')) or 0.0)) for x in ents.values() if 'max_pow' in x)
            c['max n'] += 1; ok = abs(num(n['p_pow']) + s - num(n['max'])) <= 0.0035; c['max ok'] += ok
            if not ok and len(ex['max']) < 4: ex['max'].append((nid, n['max'], round(num(n['p_pow']) + s, 3)))
        lv = num(n.get('local_value')) or 0.0; cur = num(n.get('current')); ret = num(n.get('retention')); o = num(n.get('outgoing'))
        rp = num(n.get('retain_power')); pl = num(n.get('pull_power'))
        if cur is not None and ret is not None:
            c['current n'] += 1; c['current ok'] += abs(cur - (lv + in_sum[nid]) * ret) <= max(0.0015, 0.001 * abs(cur))
            if o is not None:
                c['outgoing n'] += 1; c['outgoing ok'] += abs(o - ((lv + in_sum[nid]) - cur)) <= max(0.0015, 0.001 * abs(o))
        if None not in (rp, pl, ret) and rp + pl > 0:
            c['retention n'] += 1; c['retention ok'] += abs(ret - rp / (rp + pl)) <= 0.0011
        # links
        outs = OUT.get(nid, [])
        if not outs or o is None: continue
        sp = [num(x) for x in lst(n.get('steer_power'))]
        c['nodes with links'] += 1
        c['vao==out'] += abs((num(n.get('value_added_outgoing')) if n.get('value_added_outgoing') is not None else -1) - o) <= 0.0005
        sv = sa = 0.0; nlk = 0
        for i, to in enumerate(outs):
            L = inc.get((nid, to))
            if not L or i >= len(sp): continue
            val = sum(v for v, a in L); add = sum(a for v, a in L); w = sp[i]; nlk += 1; sv += val; sa += add
            c['links'] += 1
            c['id1 ok'] += (o * w - 0.002 <= val - add <= o * (w + 0.001) + 0.002)
            st = [num(x.get('add')) or 0.0 for x in ents.values() if 'type' in x and 'add' in x and int(num(x.get('steer_power')) or 0) == i]
            al = [num(x.get('add')) or 0.0 for x in ents.values() if 'add' in x and int(num(x.get('steer_power')) or 0) == i]
            pred_t = o * w * sum(st); pred_a = o * w * sum(al)
            c['id2 strict(0.0025) type'] += abs(add - pred_t) <= 0.0025
            c['id2 strict(0.0025) any-add'] += abs(add - pred_a) <= 0.0025
            if abs(add - pred_t) > 0.0025 and len(ex['id2 type']) < 4: ex['id2 type'].append((nid, to, round(o, 3), w, st, add))
        if nlk and sp:
            c['tight ok'] += abs((sv - sa) - o) <= o * (1 - sum(sp)) + 0.003 * nlk + 0.001 * o * nlk
            c['strict sv-sa'] += abs(sv - sa - o) <= 0.0015 * nlk
            c['strict sv'] += abs(sv - o) <= 0.0015 * nlk
            c['nodes any link add>0'] += sa > 0
            c[f'wsum={round(sum(sp), 3)}'] += 1
    # prev rule
    T = E
    for B in ns:
        outs = OUT.get(B, []); sp = [num(x) for x in lst(ns[B].get('steer_power'))]
        cand = {t for t, x in T[B].items() if is_entry(x)}
        for Dn in outs:
            for t, x in T.get(Dn, {}).items():
                if (num(x.get('province_power')) or 0.0) >= 10: cand.add(t)
        for t in cand:
            rec = num(T[B].get(t, {}).get('prev')) or 0.0
            ung = gat = 0.0; ships = 0.0
            for i, Dn in enumerate(outs):
                x = T.get(Dn, {}).get(t)
                if not x: continue
                p = num(x.get('province_power')) or 0.0
                if p >= 10:
                    ung += tr3(p, div=5)
                    if i < len(sp) and sp[i] > 0: gat += tr3(p, div=5)
                    ships += num(x.get('ship_power')) or 0.0
            c['prev cand'] += 1
            c['prev ungated ok'] += abs(ung - rec) <= 0.0005
            c['prev gated ok'] += abs(gat - rec) <= 0.0005
            if abs(gat - rec) > 0.0005:
                c['gate fails'] += 1; c['gate fails & ungated ok'] += abs(ung - rec) <= 0.0005
            if ships > 0 and B != 'polynesia_node':
                c['ship entries'] += 1; c['ship entries ungated ok'] += abs(ung - rec) <= 0.0005
                if t == 'MOR': c['ship entries MOR'] += 1; c['ship entries MOR ok'] += abs(ung - rec) <= 0.0005
    return c, ex

if __name__ == '__main__':
    pool = {e['id']: e for e in common.entries()}
    ids = sys.argv[1].split(',') if len(sys.argv) > 1 else list(pool)
    res = {}
    for i in ids:
        c, ex = run(pool[i]); res[i] = (pool[i]['date'], dict(c), {k: v for k, v in ex.items()})
        print(i, pool[i]['date'], flush=True)
    json.dump(res, open('/tmp/eu4research/ver2_identities.json', 'w'), indent=1, default=str)
