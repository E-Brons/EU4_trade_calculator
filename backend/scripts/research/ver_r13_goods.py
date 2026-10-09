import sys, pickle, collections, statistics
sys.path.insert(0, 'scripts/research')
import common
CP = pickle.loads((common.CACHE / 'ver_change_price.pkl').read_bytes()); E = {e['id']: e for e in common.entries()}
goods = [k for k, _ in CP['S01']]
# gulf_of_aden S01
n = [x for x in common.nodes(E['S01']) if x['definitions'] == 'gulf_of_aden'][0]
pr = [p for _, p in CP['S01']]; s = sum(a * p for a, p in zip(n['trade_goods_size'], pr)) / 12
print('S01 gulf_of_aden formula', round(s, 3), 'stored', n['local_value'], 'incense size', n['trade_goods_size'][26])
worst = 0
for sid in [f'S{i:02d}' for i in range(1, 36)]:
    pr = [p for _, p in CP[sid]]
    for n in common.nodes(E[sid]):
        if 'local_value' not in n or 'trade_goods_size' not in n: continue
        s = sum(a * p for a, p in zip(n['trade_goods_size'], pr)) / 12; worst = max(worst, abs(s - n['local_value']))
print('max |formula - stored| over S01-S35', round(worst, 3))
print('S42 fur', dict(CP['S42'])['fur'], 'S37 copper/paper', dict(CP['S37'])['copper'], dict(CP['S37'])['paper'])
# size vs 0.2*sum(base_production)
for sid in ['S01', 'S14', 'S36', 'S42', 'S60']:
    prov = common.block(E[sid], 'provinces'); agg = collections.defaultdict(float)
    for p in prov.values():
        if isinstance(p, dict) and p.get('trade') and p.get('trade_goods') and 'base_production' in p: agg[(p['trade'], p['trade_goods'])] += p['base_production']
    rat = collections.defaultdict(list)
    for n in common.nodes(E[sid]):
        for i, g in enumerate(goods):
            a = n['trade_goods_size'][i]
            if a > 0 and agg.get((n['definitions'], g), 0) > 0: rat[g].append(a / (0.2 * agg[(n['definitions'], g)]))
    med = {g: round(statistics.median(v), 3) for g, v in rat.items()}
    off = {g: m for g, m in med.items() if abs(m - 1) > 0.005}
    print(sid, 'goods with ratio data', len(med), 'median ratio != 1:', off)
