"""Loader for the R07/R08/R12 analyses: per save, nodes with entries, graph links."""
import sys, json, re
sys.path.insert(0, '/tmp/eu4research/repo/backend/scripts/research')
import common
from common import as_list

TAG = re.compile(r'^[A-Z0-9]{2,4}$')
GRAPH = json.load(open('/Users/elkanabronstein/myProjects/EU4_Trade_calculator/backend/data/tradenodes.json'))['nodes']
OUT = {k: [o['target'] for o in v['outgoing']] for k, v in GRAPH.items()}

def f(x, d=None):
    try: return float(x)
    except (TypeError, ValueError): return d

def load(entry):
    ns = common.nodes(entry)
    order = [n['definitions'] for n in ns]
    res = []
    for n in ns:
        ents = {k: v for k, v in n.items() if TAG.match(k) and isinstance(v, dict)}
        res.append(dict(id=n['definitions'], raw=n, ents=ents, links=OUT.get(n['definitions'], []),
                        w=[float(x) for x in as_list(n.get('steer_power'))],
                        incoming=[(order[int(i['from'])-1], float(i['value']), float(i.get('add', 0))) for i in as_list(n.get('incoming')) if isinstance(i, dict)]))
    return res, order

def all_saves():
    for e in common.entries():
        yield e, load(e)[0]
