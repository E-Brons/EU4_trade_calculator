"""Second pass: misc checks (lucky tags per save, per-save residual counts, DAN/SPA entries, genua downstream, per-frigate direct estimate)."""
import sys
sys.path.insert(0, 'scripts/research')
import common, ver2_r11_a as V, ver2_r11_b as B, ver2_r11_c as C, ver2_r11_d as D
from collections import Counter, defaultdict
es = {e['id']: e for e in common.entries()}
# lucky tags straight from the countries block
for s in C.SAVES:
    cs = common.block(es[s], 'countries')
    print(s, 'luck=yes tags:', sorted(t for t, c in cs.items() if isinstance(c, dict) and c.get('luck') == 'yes' or (isinstance(c, dict) and c.get('luck') is True)))
# per-save residual counts, class = has_trader
data = {s: C.load(s) for s in C.SAVES}
for s in C.SAVES:
    byc = defaultdict(lambda: defaultdict(list))
    for (tag, node), x in data[s].items():
        if x['light'] == 0: byc[tag][x['cls'][0]].append(round(x['mp'] - x['pp'] - x['prev'] - x['cap'] - x['mods'], 3))
    n = ok = 0
    for (tag, node), x in data[s].items():
        if x['light'] == 0 or not byc[tag].get(x['cls'][0]): continue
        R = Counter(byc[tag][x['cls'][0]]).most_common(1)[0][0]
        n += 1; ok += abs(x['mp'] - x['pp'] - x['prev'] - x['cap'] - x['mods'] - x['sp'] - R) <= 0.0025
    print(s, 'residual check (class = has_trader):', ok, 'of', n)
# ships-only pair classes
# DAN / SPA entries
rows = B.collect()
for t in ('DAN', 'SPA', 'HOL'):
    print(t, [(r['save'], r['node'], r['f'], r['status']) for r in rows if r['tag'] == t])
# genua downstream for TUR collectors in S79
M = D.model('S79')
coll = {n['definitions'] for n in common.nodes(es['S79']) if isinstance(n.get('TUR'), dict) and 'total' in n['TUR']}
print('S79 TUR collecting nodes', sorted(coll), ' downstream of genua:', sorted(D.down('genua')), ' intersection:', sorted(coll & D.down('genua')))
genua = [r for r in rows if r['save'] == 'S79' and r['tag'] == 'TUR' and r['node'] == 'genua']
print('S79 TUR genua entry', genua[0]['n'] if genua else None, 'ships')
# direct-node per-frigate estimate: +1 frigate (3.5 * f * max_demand added to val) at nodes where TUR collects
def per_frigate(sid, node):
    n = [x for x in common.nodes(es[sid]) if x['definitions'] == node][0]
    c = n['TUR']
    val = float(c['val']); md = float(c['max_demand']); eff = val - float(c.get('t_out', 0)) + float(c.get('t_in', 0)); money = float(c['money']); share = float(c['total'])
    ret = float(n['retain_power']); pul = float(n['pull_power']); cur = float(n['current'])
    X = money / share if share else 0
    gross = cur * (ret + pul) / ret
    f = (float(c['ship_power']) / 1.0)
    d = 3.5 * md    # frigate, f = 1 for TUR
    eff2 = eff + d; ret2 = ret + d
    share2 = gross * eff2 / (ret2 + pul)
    return (share2 - gross * eff / (ret + pul)) * (1 + X), (1 + X)
for sid, nodes in (('U04', ['comorin_cape', 'gujarat', 'the_moluccas']), ('U05', ['comorin_cape', 'gulf_of_aden', 'gujarat'])):
    for nd in nodes:
        try: print(sid, nd, 'direct d(money) per extra frigate (closed form, 1+X=%.3f): %+.3f' % (per_frigate(sid, nd)[1], per_frigate(sid, nd)[0]))
        except Exception as ex: print(sid, nd, 'ERR', ex)
