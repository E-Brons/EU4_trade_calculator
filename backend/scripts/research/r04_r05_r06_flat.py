"""Flat table of every (save, node, tag) entry with all raw keys + node recorded fields. Cached in /tmp/eu4research/cache/flat_r456.pkl."""
import sys, pickle, re
sys.path.insert(0, '/tmp/eu4research/repo/backend/scripts/research')
import common
from common import as_list
from app.trade import game_data
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
F = common.CACHE / 'flat_r456.pkl'

def build():
    g = game_data.graph()
    rows = []; nodes = []
    for e in common.entries():
        ns = common.nodes(e)
        order = [n['definitions'] for n in ns]
        for n in ns:
            nid = n['definitions']
            nd = {k: v for k, v in n.items() if not (TAG.match(k) and isinstance(v, dict))}
            nd['sid'] = e['id']; nd['date'] = e['date']; nd['order'] = order
            nodes.append(nd)
            for k, v in n.items():
                if TAG.match(k) and isinstance(v, dict):
                    r = dict(v); r['sid'] = e['id']; r['node'] = nid; r['tag'] = k; r['date'] = e['date']
                    rows.append(r)
    F.write_bytes(pickle.dumps((rows, nodes)))

def load():
    if not F.exists(): build()
    return pickle.loads(F.read_bytes())

if __name__ == '__main__':
    rows, nodes = load(); print(len(rows), len(nodes))
