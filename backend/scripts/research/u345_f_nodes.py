"""f per node for leaderless ship entries: is the deviation a node effect?"""
import pickle
from collections import Counter, defaultdict
rows = pickle.load(open('/tmp/eu4research/cache/u345_f_rows.pkl', 'rb'))
by = defaultdict(list)
for x in rows:
    if any(f['leader'] for f in x['fleets']): continue
    by[x['node']].append((x['sid'], x['tag'], x['f'], x['n']))
print('leaderless entries:', sum(len(v) for v in by.values()), 'nodes:', len(by))
for node, v in sorted(by.items()):
    fs = Counter(f for _, _, f, _ in v)
    if set(fs) != {1.0}:
        print(node, dict(fs))
        for r in sorted(v): print('   ', r)
print('nodes where ALL leaderless entries have f == 1:', sum(1 for v in by.values() if {f for _, _, f, _ in v} == {1.0}))
