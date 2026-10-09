"""R09 node-field claims on the new saves: max = p_pow + sum(max_pow - prev - province_power); highest_power = strongest single province's power (top_provinces_values[0]);
R04: transfer flags. Run from backend/."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list
from u345_pipe_prev import NEW, tags, ent
pool = {e['id']: e for e in common.entries() + NEW}
for i in ('S14', 'S79', 'S80', 'U03', 'U04', 'U05'):
    c = collections.Counter(); ex = []
    for n in common.nodes(pool[i]):
        if 'max' in n and 'p_pow' in n:
            T = tags(n)
            s = sum(t.get('max_pow', 0.0) - t.get('prev', 0.0) - t.get('province_power', 0.0) for t in T.values() if 'max_pow' in t)
            c['max n'] += 1; ok = abs(n['p_pow'] + s - n['max']) <= 0.0035; c['max ok'] += ok
            if not ok and len(ex) < 3: ex.append((n['definitions'], n['max'], round(n['p_pow'] + s, 3)))
        tv = as_list(n.get('top_provinces_values'))
        if tv and 'highest_power' in n:
            c['highest n'] += 1; c['highest ok'] += abs(max(tv) - n['highest_power']) <= 0.0015
    print(i, pool[i]['date'], dict(c), ex)
