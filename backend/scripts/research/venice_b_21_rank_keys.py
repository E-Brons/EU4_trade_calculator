"""R08 Q2: which ordering key reproduces add = a_c/rank on the played saves (and on Venice)?"""
import sys
sys.path.insert(0, 'scripts/research')
import common, venice_load as V, venice_b_5_rank as R
R.KEYS['prev_or_pow'] = lambda e: -e.get('prev', e.get('max_pow', 0))
R.KEYS['pow_no_ship'] = lambda e: -(e.get('max_pow', 0) - e.get('ship_power', 0))
R.KEYS['val_no_ship'] = lambda e: -(e.get('val', 0) - e.get('ship_power', 0) * (e.get('val', 0) / e.get('max_pow', 1) if e.get('max_pow') else 1))
R.KEYS['max_demand'] = lambda e: -e.get('max_demand', 0)
sets = {}
for e in common.entries():
    if e['id'] in ('S79', 'S80', 'U06'): sets[e['id']] = common.nodes(e)
for tag in ('1444_12_01', '1445_04_01', '1445_07_02'):
    p = [x for x in V.files() if x.stem.endswith(tag)][0]; sets['V' + tag] = V.nodes(p)
for name, ns in sets.items():
    print(name, {k: R.test(ns, k)[:2] for k in ('val', 'max_pow', 'prev', 'prev_or_pow', 'pow_no_ship', 'val_no_ship', 'max_demand')})
