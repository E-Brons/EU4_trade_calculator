"""Builds cache/master_<id>.pkl: per save, trade nodes + country trade fields + province->node home, used by the R01/R02/R10 analyses.
Usage: python r01_r02_r10_build.py [ID ...]   (default: all)"""
import sys, pickle, os
sys.path.insert(0, os.path.dirname(__file__))
import common
from common import as_list

CKEYS = ['trade_port', 'capital', 'trade_embargoed_by', 'trade_embargoes', 'mercantilism', 'num_ships_protecting_trade',
         'government_rank', 'overlord', 'subjects', 'transfer_trade_power_from', 'transfer_trade_power_to', 'prestige',
         'current_power_projection', 'government', 'technology', 'active_idea_groups', 'ideas', 'religion', 'estate']

def build(e):
    out = common.CACHE / f"master_{e['id']}.pkl"
    if out.exists():
        return
    ns = common.nodes(e)
    cs = common.block(e, 'countries')
    ps = common.block(e, 'provinces')
    prov_node = {}
    for k, p in ps.items():
        if isinstance(p, dict) and 'trade' in p:
            prov_node[abs(int(k))] = p['trade']
    countries = {}
    for tag, c in cs.items():
        if not isinstance(c, dict):
            continue
        d = {k: c.get(k) for k in CKEYS if k in c}
        if 'trade_port' in c:
            try:
                d['home_node'] = prov_node.get(int(c['trade_port']))
            except Exception:
                pass
        countries[tag] = d
    master = dict(id=e['id'], tag=e['tag'], date=e['date'], nodes=ns, countries=countries,
                  node_order=[n['definitions'] for n in ns])
    tmp = out.with_suffix(f'.{os.getpid()}.tmp')
    tmp.write_bytes(pickle.dumps(master)); tmp.replace(out)

if __name__ == '__main__':
    want = set(sys.argv[1:])
    for e in common.entries():
        if not want or e['id'] in want:
            build(e); print(e['id'], flush=True)
