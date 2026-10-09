"""Consistency of a save with itself between tick-time fields (top_power list, incoming.add) and event-time fields (entries). Run from backend/.
For each node: tags in top_power (or top_power_values length) without an entry carrying data (ent) at the node; and link adds with no steerer-add explanation."""
import sys, collections
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from common import as_list
from u345_pipe_prev import NEW, tags, ent
pool = {e['id']: e for e in common.entries() + NEW}
def check(e):
    c = collections.Counter(); ex = []
    for n in common.nodes(e):
        T = tags(n); tp = as_list(n.get('top_power')); tv = as_list(n.get('top_power_values'))
        c['nodes'] += 1
        miss = [t for t in tp if t not in T or not ent(T[t])]
        if miss: c['nodes with top_power tag lacking entry'] += 1; ex.append((n['definitions'], miss, [tv[tp.index(t)] for t in miss]))
        # top_power_values vs val-t_out+t_in for the tags present
        for t, v in zip(tp, tv):
            if t in T and 'val' in T[t]:
                eff = T[t]['val'] - T[t].get('t_out', 0.0) + T[t].get('t_in', 0.0)
                c['top values compared'] += 1; c['top values == eff'] += abs(eff - v) <= 0.0015
    return c, ex
for i in ('S14', 'S79', 'S80', 'U03', 'U04', 'U05'):
    c, ex = check(pool[i]); print(i, pool[i]['date'], dict(c), ex[:4])
