"""Own re-implementation of R08/R12 link and tick identities on any set of saves. Run from backend/.
Claims: link value = out*w + add; add = out*w*sum(add of steerers on the link); value_added_outgoing == outgoing; sum(value)-sum(add) ~ out*sum(w);
current = (local_value + sum incoming.value)*retention; outgoing = gross - current; retention = retain/(retain+pull); val = trunc3(max_pow*max_demand)."""
import sys, collections, math
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list
from u345_pipe_prev import NEW, out, tags, ent

def f(x, d=None):
    try: return float(x)
    except (TypeError, ValueError): return d

def run(e):
    nl = common.nodes(e); order = [n['definitions'] for n in nl]; ns = {n['definitions']: n for n in nl}
    c = collections.Counter(); ex = collections.defaultdict(list)
    inc = {}
    for Dn, n in ns.items():
        for i in as_list(n.get('incoming')):
            if isinstance(i, dict):
                fr = int(i['from']); B = order[fr - 1]
                inc.setdefault((B, Dn), []).append((f(i.get('value'), 0.0), f(i.get('add'), 0.0)))
    for B, n in ns.items():
        o = f(n.get('outgoing')); sp = [f(x) for x in as_list(n.get('steer_power'))]
        T = tags(n)
        # node identities
        lv = f(n.get('local_value'), 0.0); cur = f(n.get('current')); ret = f(n.get('retention')); rp = f(n.get('retain_power')); pp = f(n.get('pull_power'))
        sum_in = sum(v for (b, d), L in inc.items() if d == B for v, a in L)
        if cur is not None and ret is not None:
            c['current n'] += 1; ok = abs(cur - (lv + sum_in) * ret) <= max(0.0015, 0.001 * abs(cur)); c['current ok'] += ok
            if not ok and len(ex['current']) < 3: ex['current'].append((B, cur, round((lv + sum_in) * ret, 3)))
            if o is not None:
                c['outgoing n'] += 1; ok = abs(o - ((lv + sum_in) - cur)) <= max(0.0015, 0.001 * abs(o)); c['outgoing ok'] += ok
                if not ok and len(ex['outgoing']) < 3: ex['outgoing'].append((B, o, round((lv + sum_in) - cur, 3)))
        if rp is not None and pp is not None and ret is not None and (rp + pp) > 0:
            c['retention n'] += 1; c['retention ok'] += abs(ret - rp / (rp + pp)) <= 0.0011
        for tag, t in T.items():
            if 'max_pow' in t and 'max_demand' in t and 'val' in t:
                c['val n'] += 1; c['val ok'] += abs(math.trunc(f(t['max_pow']) * f(t['max_demand']) * 1000 + 1e-9) / 1000 - f(t['val'])) <= 0.0005 + 1e-9
        if not out.get(B) or o is None: continue
        c['nodes with links'] += 1
        c['vao==out'] += abs(f(n.get('value_added_outgoing'), -1) - o) <= 0.0005
        sv = sa = 0.0; nl_ = 0
        for i, Dn in enumerate(out[B]):
            L = inc.get((B, Dn))
            if not L or i >= len(sp): continue
            val = sum(v for v, a in L); add = sum(a for v, a in L); w = sp[i]
            nl_ += 1; sv += val; sa += add
            c['links'] += 1
            c['id1 ok'] += (o * w - 0.002 <= val - add <= o * (w + 0.001) + 0.002)
            adds_all = [f(t.get('add'), 0.0) for t in T.values() if 'add' in t and int(f(t.get('steer_power'), 0)) == i]
            adds_typ = [f(t.get('add'), 0.0) for t in T.values() if 'add' in t and 'type' in t and int(f(t.get('steer_power'), 0)) == i]
            for nm, lst in (('all', adds_all), ('type', adds_typ)):
                tol = 0.002 + o * 0.001 * sum(lst) + o * w * 0.0005 * len(lst) + 0.001 * o * w
                ok = abs(add - o * w * sum(lst)) <= tol; c[f'id2 {nm} ok'] += ok
                if not ok and len(ex['id2 ' + nm]) < 3: ex['id2 ' + nm].append((B, Dn, round(o, 3), w, lst, add))
        if nl_ and sp:
            strict = abs(sv - o) <= 0.0015 * nl_; c['sum(value)==out strict'] += strict
            c['sum(value)-sum(add)==out strict'] += abs(sv - sa - o) <= 0.0015 * nl_
            c['has add>0'] += sa > 0
            c['tight bound ok'] += abs((sv - sa) - o) <= o * (1 - sum(sp)) + 0.003 * nl_ + 0.001 * o * nl_
            c['wsum'] = c['wsum']
            c[f'wsum={round(sum(sp),3)}'] += 1
    return c, ex

if __name__ == '__main__':
    ids = sys.argv[1].split(',') if len(sys.argv) > 1 else ['S14', 'S79', 'S80', 'U03', 'U04', 'U05']
    pool = {e['id']: e for e in common.entries() + NEW}
    for i in ids:
        c, ex = run(pool[i])
        print(i, pool[i]['date'])
        print('   ', {k: v for k, v in c.items() if not k.startswith('wsum')})
        print('    weight sums:', {k[5:]: v for k, v in c.items() if k.startswith('wsum=')})
        for k, v in ex.items(): print('    first fails', k, v)
