"""R08/R12 bridge: which node fields change between saves of the same month (no tick)? Count by field name; separate steer_power and incoming.add/value."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V, venice_diff as D
import re
pairs = [('1444_11_11', '1444_11_14'), ('1444_11_14', '1444_11_30'), ('1444_12_01', '1444_12_02'), ('1444_12_02', '1444_12_11'), ('1444_12_11', '1444_12_31'),
         ('1445_01_01', '1445_01_02'), ('1445_01_02', '1445_01_15'), ('1445_01_15', '1445_01_24'), ('1445_01_24', '1445_01_30'), ('1445_01_30', '1445_01_31'),
         ('1445_02_01', '1445_02_03'), ('1445_02_03', '1445_02_10'), ('1445_02_10', '1445_02_17'), ('1445_02_17', '1445_02_28'), ('1445_03_01', '1445_03_31')]
by = {p.stem[6:]: p for p in V.files()}
tot = collections.Counter()
for a, b in pairs:
    na, nb = D.nodeflat(by[a]), D.nodeflat(by[b])
    keys = [k for k in set(na) | set(nb) if na.get(k) != nb.get(k)]
    c = collections.Counter(re.sub(r'\[\d+\]', '[]', k.split('/')[-1]) for k in keys)
    tot.update(c)
    print(a, '->', b, len(keys), dict(c.most_common(6)))
print('TOTAL by field name:', dict(tot.most_common(20)))
print('steer_power / incoming changed mid-month:', {k: v for k, v in tot.items() if k in ('steer_power', 'add', 'value', 'incoming', 'outgoing', 'current', 'local_value', 'from')})
