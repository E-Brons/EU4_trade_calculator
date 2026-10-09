"""Independent verification (R13 C-01, R09 C-14): local_value = sum(trade_goods_size[i]*current_price[i])/12."""
import sys, re, pickle, collections, os
sys.path.insert(0, 'scripts/research')
import common
from app.trade import savefile
from app.parsing.clausewitz import parse
PLAYED = {'S79', 'S80', 'U01', 'U02'}
cache = common.CACHE / 'ver_change_price.pkl'
if cache.exists(): CP = pickle.loads(cache.read_bytes())
else:
    CP = {}
    for e in common.entries():
        t = common._text(e)
        raw = savefile.extract_top_level_block(t.gamestate, 'change_price')
        tree = parse(raw[1:-1])
        CP[e['id']] = [(k, v.get('current_price') if isinstance(v, dict) else None) for k, v in tree.items()]
        tp = savefile.extract_top_level_block(t.gamestate, 'tradegoods_total_produced')
        CP[e['id'] + '_ttp'] = [float(x) for x in re.findall(r'-?\d+\.?\d*', tp)] if tp else None
    cache.write_bytes(pickle.dumps(CP))
C = collections.Counter(); inc_idx = None; F = collections.defaultdict(list)
orders = collections.Counter(tuple(k for k, _ in CP[e['id']]) for e in common.entries())
print('distinct goods orders', len(orders)); order = list(orders.most_common(1)[0][0]); print(len(order), order)
for e in common.entries():
    sid = e['id']; cp = CP[sid]; price = [p for _, p in cp]
    assert len(price) == 33, (sid, len(price))
    ii = [k for k, _ in cp].index('incense')
    for n in common.nodes(e):
        if 'trade_goods_size' not in n or 'local_value' not in n: continue
        C['nodes'] += 1
        s = sum(a * p for a, p in zip(n['trade_goods_size'], price)) / 12
        ok = abs(s - n['local_value']) <= 0.002
        C['ok'] += ok
        if not ok:
            has_inc = n['trade_goods_size'][ii] > 0
            C['fail_with_incense'] += has_inc; C['fail_no_incense'] += not has_inc
            if not has_inc: F['noinc'].append((sid, n['definitions'], round(s, 3), n['local_value']))
            else:
                extra = (n['local_value'] - s) * 12 / n['trade_goods_size'][ii]
                C['extra_price_x12:' + str(round(extra, 2))] += 1
        C['nodes_with_incense'] += n['trade_goods_size'][ii] > 0
    # ttp
    ttp = CP.get(sid + '_ttp')
    if ttp:
        tot = [0.0] * 33
        for n in common.nodes(e):
            for i, a in enumerate(n.get('trade_goods_size', [])): tot[i] += a
        diffs = [i for i in range(33) if abs(tot[i] - ttp[i]) > 0.01]
        C['ttp_only_last_differs'] += diffs in ([32], [])
        C['ttp_saves'] += 1
    # price of incense and gold
    C['gold_price0'] += price[order.index('gold')] == 0
print({k: v for k, v in C.items() if not k.startswith('extra_price')})
print('fail-no-incense', len(F['noinc']), collections.Counter(x[0] for x in F['noinc']), F['noinc'][:12])
ex = sorted(((k[len('extra_price_x12:'):], v) for k, v in C.items() if k.startswith('extra_price')), key=lambda x: -x[1])[:8]; print('incense extra', ex)
print('incense price per save (counter)', collections.Counter(CP[e['id']][[k for k, _ in CP[e['id']]].index('incense')][1] for e in common.entries()))
print('S42 prices', [(k, p) for k, p in CP['S42'][:5]], 'S01', [(k, p) for k, p in CP['S01'] if k in ('grain', 'cloth', 'fur', 'ivory', 'cloves', 'paper', 'incense')])
