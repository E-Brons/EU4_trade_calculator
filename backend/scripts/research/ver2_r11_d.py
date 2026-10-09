"""Second pass U-3: recorded change of node retain/pull power vs the countries' own change of effective power (independent)."""
import sys
sys.path.insert(0, 'scripts/research')
import common
from collections import defaultdict, Counter
from app.parsing.tradenodes import load_trade_graph
A = common.as_list
G = load_trade_graph()
es = {e['id']: e for e in common.entries()}
f = lambda x: float(x) if x is not None else 0.0
_down = {}
def down(n):
    if n in _down: return _down[n]
    seen = set(); st = list(G.outgoing(n))
    while st:
        m = st.pop()
        if m in seen: continue
        seen.add(m); st.extend(G.outgoing(m))
    _down[n] = seen
    return seen

def model(sid):
    nodes = common.nodes(es[sid])
    coll = defaultdict(set)
    for n in nodes:
        for tag, c in n.items():
            if isinstance(c, dict) and 'total' in c: coll[tag].add(n['definitions'])
    out = {}
    for n in nodes:
        nid = n['definitions']; ret = pul = 0.0; who = {}
        for tag, c in n.items():
            if not isinstance(c, dict) or len(set(c) - {'max_demand'}) == 0: continue
            if not (set(c) & {'val', 't_in', 't_out'}): continue
            eff = f(c.get('val')) - f(c.get('t_out')) + f(c.get('t_in'))
            collecting = 'total' in c; steering = 'type' in c
            pulling = steering or (not collecting and bool(coll[tag] & down(nid)))
            if collecting: ret += eff
            if pulling: pul += eff
            who[tag] = (eff, 'R' if collecting else '', 'P' if pulling else '')
        out[nid] = dict(rec_ret=f(n.get('retain_power')), rec_pull=f(n.get('pull_power')), ret=ret, pul=pul, who=who)
    return out

if __name__ == '__main__':
    M = {s: model(s) for s in ('S79', 'S80', 'U03', 'U04', 'U05')}
    for s, m in M.items():
        nr = sum(1 for x in m.values() if abs(x['rec_ret'] - x['ret']) <= 0.01); npl = sum(1 for x in m.values() if abs(x['rec_pull'] - x['pul']) <= 0.01)
        print(s, 'nodes', len(m), 'retain rule ok', nr, 'pull rule ok', npl)
    def delta(a, b, node, tag='TUR'):
        x, y = M[a][node], M[b][node]
        wa, wb = x['who'].get(tag, (0, '', '')), y['who'].get(tag, (0, '', ''))
        pool = 'rec_ret' if wb[1] == 'R' else 'rec_pull'
        d_rec = y[pool] - x[pool]
        d_own = wb[0] - wa[0]
        pool2 = 'ret' if wb[1] == 'R' else 'pul'
        # others' change inside the same pool by the rule
        oth = 0.0
        for t in set(x['who']) | set(y['who']):
            if t == tag: continue
            ea, ra, pa = x['who'].get(t, (0, '', '')); eb, rb, pb = y['who'].get(t, (0, '', ''))
            flag = 1 if pool2 == 'ret' else 2
            oth += (eb if (rb, pb)[flag - 1] else 0.0) - (ea if (ra, pa)[flag - 1] else 0.0)
        print(f'{a}->{b} {node:16s} TUR flags {wa[1:]}->{wb[1:]} pool {pool}: recorded d {d_rec:+.3f}  TUR own d {d_own:+.3f}  others(rule) d {oth:+.3f}  residual rec-own-others {d_rec - d_own - oth:+.3f}')
    for node in ('hormuz', 'basra', 'gulf_of_aden', 'malacca', 'the_moluccas', 'gujarat', 'comorin_cape'):
        delta('U03', 'U04', node)
    for node in ('philippines', 'the_moluccas', 'gulf_of_aden', 'hormuz'):
        delta('U04', 'U05', node)
