"""Independent check: pull_power rule (R03 vs extended with downstream steering) and power_fraction (R04 Q6)."""
import sys, json, collections
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

G = json.load(open(Path(__file__).resolve().parents[2] / 'data' / 'tradenodes.json'))['nodes']
out = {n: [o['target'] for o in v['outgoing']] for n, v in G.items()}
down = {}
def dn(n):
    if n in down: return down[n]
    s = set()
    for t in out.get(n, []): s.add(t); s |= dn(t)
    down[n] = s; return s
def q(x): return int(round(float(x) * 1000))
def thou(x): return D(repr(float(x)))
def tr3(d): return int(d.quantize(D('0.001'), rounding=ROUND_DOWN) * 1000)
def ent(c): return isinstance(c, dict) and bool(set(c) - {'max_demand'})

res = collections.Counter(); bad_r03 = []; bad_ext = []
pf = collections.Counter(); pf_bad = []
for e in common.entries():
    sid = e['id']; ns = common.nodes(e)
    coll = collections.defaultdict(set); steer = collections.defaultdict(set)
    for n in ns:
        for tag, c in n.items():
            if isinstance(c, dict) and tag.upper() == tag and len(tag) <= 4:
                if 'total' in c: coll[tag].add(n['definitions'])
                if 'type' in c: steer[tag].add(n['definitions'])
    for n in ns:
        nid = n['definitions']
        if 'pull_power' not in n:
            pass
        p3 = p_ext = 0.0
        for tag, c in (n.items() if 'pull_power' in n else []):
            if not (isinstance(c, dict) and tag.upper() == tag and len(tag) <= 4 and ent(c)): continue
            eff = c.get('val', 0) - c.get('t_out', 0) + c.get('t_in', 0)
            here = 'total' in c; st = 'type' in c
            dcoll = bool(coll[tag] & dn(nid)); dst = bool(steer[tag] & dn(nid))
            if st or (not here and dcoll): p3 += eff
            if st or (not here and (dcoll or dst)): p_ext += eff
        if 'pull_power' in n:
            res['nodes'] += 1
            if abs(n['pull_power'] - p3) > 0.0105: res['R03 mismatch'] += 1; bad_r03.append((sid, nid))
            if abs(n['pull_power'] - p_ext) > 0.0105: res['ext mismatch'] += 1; bad_ext.append((sid, nid))
        # power_fraction = trunc3((val - t_out + t_in)/retain_power)
        rp = n.get('retain_power')
        for tag, c in n.items():
            if isinstance(c, dict) and 'power_fraction' in c and rp:
                eff = thou(c['val']) - thou(c.get('t_out', 0)) + thou(c.get('t_in', 0))
                ok = tr3(eff / thou(rp)) == q(c['power_fraction'])
                kind = 'giver' if 't_out' in c else ('receiver' if 't_in' in c else 'plain')
                pf[(kind, ok)] += 1
                if not ok: pf_bad.append((sid, nid, tag))
print(dict(res)); print('R03 mismatching nodes', bad_r03[:10]); print('ext mismatching', bad_ext[:10])
print('power_fraction', dict(pf), pf_bad[:10])
