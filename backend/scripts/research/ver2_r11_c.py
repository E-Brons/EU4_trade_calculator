"""Second pass: U-2 (ship_power inside max_pow, marginal ship pairs) and U-3 (node power change) - independent code."""
import sys
sys.path.insert(0, 'scripts/research')
import common, ver2_r11_a as V
from collections import Counter, defaultdict
from app.parsing.tradenodes import load_trade_graph
A = common.as_list
SAVES = ['S79', 'S80', 'U03', 'U04', 'U05']
es = {e['id']: e for e in common.entries()}
f = lambda x, d=0.0: float(x) if x is not None else d

def entry_facts(c):
    mods = sum(f(m.get('power')) for m in A(c.get('modifier')) if isinstance(m, dict))
    return dict(pp=f(c.get('province_power')), sp=f(c.get('ship_power')), prev=f(c.get('prev')), mp=f(c.get('max_pow')),
                md=f(c.get('max_demand')), val=f(c.get('val')), cap=5.0 if c.get('has_capital') else 0.0, mods=mods,
                cls=(bool(c.get('has_trader')), 'type' in c, 'total' in c), light=int(f(c.get('light_ship'))),
                tin=f(c.get('t_in')), tout=f(c.get('t_out')), trans=(tuple(sorted((k, f(v)) for k, v in c['t_to'].items())) if isinstance(c.get('t_to'), dict) else ()),
                collecting='total' in c, steering='type' in c)

def load(sid):
    out = {}
    for n in common.nodes(es[sid]):
        for tag, c in n.items():
            if isinstance(c, dict) and 'max_pow' in c:
                out[(tag, n['definitions'])] = entry_facts(c)
    return out

if __name__ == '__main__':
    data = {s: load(s) for s in SAVES}
    # ---- U-2 part 1: residual
    tot = ok = alt = 0; bad = []
    for s in SAVES:
        d = data[s]; byc = defaultdict(lambda: defaultdict(list))
        for (tag, node), x in d.items():
            if x['light'] == 0:
                byc[tag][x['cls']].append(round(x['mp'] - x['pp'] - x['prev'] - x['cap'] - x['mods'], 3))
        n_ok = n_tot = n_alt = 0
        for (tag, node), x in d.items():
            if x['light'] == 0 or not byc[tag].get(x['cls']): continue
            vals = Counter(byc[tag][x['cls']]); R, _ = vals.most_common(1)[0]
            resid = x['mp'] - x['pp'] - x['prev'] - x['cap'] - x['mods']
            n_tot += 1
            if abs(resid - x['sp'] - R) <= 0.0025: n_ok += 1
            else: bad.append((s, tag, node, round(resid - x['sp'] - R, 3)))
            if abs(resid - R) <= 0.0025: n_alt += 1
        print(s, 'entries with ships and ship-less reference', n_tot, 'residual==R', n_ok, 'alt (ship_power not in max_pow) fits', n_alt)
        tot += n_tot; ok += n_ok; alt += n_alt
    print('TOTAL', tot, ok, alt, 'mismatches:', bad[:10])
    # entries with ships but no reference
    print('entries with ships', sum(1 for s in SAVES for x in data[s].values() if x['light']))
    # ---- marginal pairs
    pairs = [('S79', 'S80'), ('U03', 'U04'), ('U04', 'U05'), ('U03', 'U05')]
    allp = []
    for a, b in pairs:
        n = 0
        for key in data[a].keys() & data[b].keys():
            x, y = data[a][key], data[b][key]
            if abs(x['sp'] - y['sp']) < 0.0005: continue
            same = (abs(x['pp'] - y['pp']) < 0.0005 and abs(x['prev'] - y['prev']) < 0.0005 and x['cap'] == y['cap'] and abs(x['mods'] - y['mods']) < 0.0005
                    and x['cls'][0] == y['cls'][0] and x['tin'] == y['tin'] and x['tout'] == y['tout'] and x['trans'] == y['trans'])
            if not same: continue
            n += 1
            allp.append((a, b, key, x, y))
        print(a, '->', b, 'ships-only pairs', n)
    ok_mp = sum(1 for a, b, k, x, y in allp if abs((y['mp'] - x['mp']) - (y['sp'] - x['sp'])) <= 0.0025)
    ok_val = sum(1 for a, b, k, x, y in allp if abs(y['val'] - y['mp'] * y['md']) <= 0.0015 and abs(x['val'] - x['mp'] * x['md']) <= 0.0015)
    print('pairs', len(allp), 'd(max_pow)==d(ship_power)', ok_mp, 'val==max_pow*max_demand in both saves', ok_val)
    for a, b, k, x, y in allp:
        if k[0] == 'TUR': print('  TUR', a, b, k[1], 'light', x['light'], '->', y['light'], 'dsp', round(y['sp'] - x['sp'], 3), 'val', x['val'], '->', y['val'], 'md', x['md'], y['md'], x['cls'])
    print('  max_demand unchanged (<=0.0015) in', sum(1 for a, b, k, x, y in allp if abs(x['md'] - y['md']) <= 0.0015), 'of', len(allp))
    # max ships
    mx = sorted(((x['light'], s, k) for s in SAVES for k, x in data[s].items()), reverse=True)[:4]
    print('largest entries', mx)
    print('TUR the_moluccas', {s: data[s].get(('TUR', 'the_moluccas'), {}).get('light') for s in SAVES})
