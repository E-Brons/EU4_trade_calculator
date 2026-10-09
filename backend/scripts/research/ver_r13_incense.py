import sys, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
CP = pickle.loads((common.CACHE / 'ver_change_price.pkl').read_bytes())
R = collections.Counter(); D = collections.Counter(); ex = []
for e in common.entries():
    sid = e['id']; cp = CP[sid]; price = [p for _, p in cp]; ii = 26
    assert cp[ii][0] == 'incense'
    ttp = CP[sid + '_ttp']; tot = [0.0] * 33
    for n in common.nodes(e):
        for i, a in enumerate(n.get('trade_goods_size', [])): tot[i] += a
    D[tuple(i for i in range(33) if abs(tot[i] - ttp[i]) > 0.01)] += 1
    for n in common.nodes(e):
        if 'trade_goods_size' not in n or 'local_value' not in n or n['trade_goods_size'][ii] <= 0: continue
        if sid in ('S79', 'S80', 'U01', 'U02'): continue
        s = sum(a * p for a, p in zip(n['trade_goods_size'], price)) / 12
        s10 = s + 0.1 * price[ii] * n['trade_goods_size'][ii] / 12
        R['nodes'] += 1
        R['ok_plain'] += abs(s - n['local_value']) <= 0.002
        R['ok_incense x1.1'] += abs(s10 - n['local_value']) <= 0.002
        R['ok_incense x1.1 (0.004)'] += abs(s10 - n['local_value']) <= 0.004
        if abs(s10 - n['local_value']) > 0.004: ex.append((sid, n['definitions'], round(s10, 3), n['local_value'], n['trade_goods_size'][ii]))
print(dict(R)); print('ttp diff index sets', D); print(len(ex), ex[:10])
