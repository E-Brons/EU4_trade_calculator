import sys, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
sv = collections.Counter(); bei = []
for e in common.entries():
    for n in common.nodes(e):
        for tag, c in n.items():
            if isinstance(c, dict) and set(c) <= {'max_demand', 'potential'} and 'potential' in c:
                sv[(e['id'], n['definitions'])] += 1
            if e['id'] in ('S80', 'U01') and tag == 'BEI' and isinstance(c, dict) and 'val' in c and 't_out' not in c:
                bei.append(n['definitions'])
print('saves with potential-only stubs:', sorted(set(k[0] for k in sv))[:5], '...', len(set(k[0] for k in sv)), 'saves; nodes', set(k[1] for k in sv))
print('BEI entries with val, no t_out (S80+U01):', len(bei), bei)
