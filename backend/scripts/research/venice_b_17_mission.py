"""R09: what is countries.<TAG>.trade_mission? Test: merchants / trade_mission vs count of nodes where the country has power."""
import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V
from venice_load import as_list
tag = sys.argv[1] if len(sys.argv) > 1 else '1445_04_01'
p = [x for x in V.files() if x.stem.endswith(tag)][0]
cs = V.load(p, 'countries'); ns = V.nodes(p)
cnt = collections.Counter(); cntpp = collections.Counter(); cntcoll = collections.Counter(); cnttr = collections.Counter()
for n in ns:
    for c, e in n.items():
        if isinstance(e, dict) and c.isupper():
            if 'val' in e: cnt[c] += 1
            if e.get('province_power'): cntpp[c] += 1
            if 'money' in e: cntcoll[c] += 1
            if e.get('type'): cnttr[c] += 1
rows = []
for k, c in cs.items():
    if isinstance(c, dict) and 'trade_mission' in c:
        m = c.get('merchants'); nm = len(as_list(m.get('envoy'))) if isinstance(m, dict) else 0
        rows.append((k, c['trade_mission'], nm, cnt[k], cntpp[k], cntcoll[k], cnttr[k], round(nm / c['trade_mission'], 2) if c['trade_mission'] else None))
for r in rows[:14]: print(r, '(tag, trade_mission, envoys, nodes_with_val, nodes_prov_power, collecting_nodes, steering_entries, envoys/mission)')
import statistics
for i, name in ((3, 'nodes_with_val'), (4, 'nodes_prov_power'), (5, 'collecting'), (6, 'steering')):
    ok = sum(1 for r in rows if r[7] is not None and abs(r[7] - r[i]) < 0.06)
    print(name, 'matches envoys/mission', ok, '/', len(rows))
