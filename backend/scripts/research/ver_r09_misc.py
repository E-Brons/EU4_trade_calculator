"""Independent verification: R09 Q5 (S14 alexandria), C-13 already_sent, C-14 goods sizes."""
import sys, re, math, collections, statistics
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
def t3(x): return math.floor(x * 1000 + 1e-7) / 1000
E = {e['id']: e for e in common.entries()}
ns = {n['definitions']: n for n in common.nodes(E['S14'])}; n = ns['alexandria']
es = {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}
print('sum val', round(sum(v.get('val', 0) for v in es.values()), 3), 'total', n['total'])
col = {t: v for t, v in es.items() if 'total' in v}
rp = sum(v['val'] - v.get('t_out', 0) + v.get('t_in', 0) for v in col.values()); print('retain', round(rp, 3), n['retain_power'], n['collector_power'])
for t, v in col.items():
    print(t, 'val', v['val'], 'max_pow*md', v['max_pow'], v['max_demand'], t3(v['max_pow'] * v['max_demand']), '| pf', v['power_fraction'], t3(v['val'] / rp), '| total', v['total'], t3(n['current'] * v['power_fraction']))
sp = sum(v.get('province_power', 0) for v in es.values()); ex = sum(v['max_pow'] - v.get('prev', 0) for v in es.values() if 'max_pow' in v)
print('p_pow', n['p_pow'], 'sum pp', round(sp, 3), 'max', n['max'], 'sum(max_pow-prev)', round(ex, 3), 'entries with has_capital', sum(1 for v in es.values() if v.get('has_capital')))
print('top_power', list(zip(n['top_power'], n['top_power_values']))[:4], 'top_provinces', list(zip(n['top_provinces'], n['top_provinces_values']))[:3])
print('retention quotient', n['retain_power'] / (n['retain_power'] + n['pull_power']), 'stored', n['retention'], 'local', n['local_value'], 'incoming', [i['value'] for i in n['incoming']], 'current', n['current'])
inc = sum(i['value'] for i in n['incoming']); print('(local+inc)*stored', round((n['local_value'] + inc) * n['retention'], 4), '(local+inc)*quotient', round((n['local_value'] + inc) * n['retain_power'] / (n['retain_power'] + n['pull_power']), 4))
# C-13 already_sent
K = collections.Counter(); whole = 0; tot = 0; indeg_match = 0; absent_pp = 0; absent_pp10 = 0; eq = collections.Counter()
for e in common.entries():
    for nd in common.nodes(e):
        indeg = len(nd['incoming']) if isinstance(nd.get('incoming'), list) else (1 if 'incoming' in nd else 0)
        for t, v in nd.items():
            if not (TAG.match(t) and isinstance(v, dict)): continue
            pp = v.get('province_power', 0)
            if 'already_sent' in v:
                tot += 1
                if pp > 0:
                    k = v['already_sent'] / (pp / 5)
                    if abs(k - round(k)) < 0.01 and 1 <= round(k) <= 5: whole += 1; K[round(k)] += 1
                    else: K['other'] += 1
                    if abs(k - indeg) < 0.01: indeg_match += 1
                for f in ('val', 'max_pow', 'province_power', 'money', 'total', 'prev', 't_out'):
                    if f in v and abs(v[f] - v['already_sent']) < 0.0015: eq[f] += 1
                for f in ('outgoing', 'current', 'total'):
                    if f in nd and abs(nd[f] - v['already_sent']) < 0.0015: eq['node.' + f] += 1
            elif pp > 0:
                absent_pp += 1; absent_pp10 += pp >= 10
print('already_sent entries', tot, 'k whole 1..5', whole, dict(K), 'k==in-degree', indeg_match, 'absent with pp>0', absent_pp, 'of which pp>=10', absent_pp10, 'equalities', dict(eq))
# C-14 S01 goods
nd1 = common.nodes(E['S01']); zero_idx = [i for i in range(33) if all(n_['trade_goods_size'][i] == 0 for n_ in nd1)]; print('S01 all-zero goods indices', zero_idx)
