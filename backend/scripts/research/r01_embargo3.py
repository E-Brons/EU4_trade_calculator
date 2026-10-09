"""R01 Q1: for rows with exactly one embargoer having province/ship power, solve the implied denominator D = 0.5*P/red and compare with S, 5*NH."""
import sys, os, re, collections, pickle, statistics
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
rows = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    for tag, c in m['countries'].items():
        emb = c.get('trade_embargoed_by')
        if not emb: continue
        home = c.get('home_node'); recs = []
        for n in m['nodes']:
            v = n.get(tag)
            if not (isinstance(v, dict) and 'max_demand' in v): continue
            ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
            away = ('total' in v) and not v.get('has_capital')
            dom = (n['definitions'] == home) or ((n.get('top_provinces') or [None])[0] == tag)
            recs.append(dict(node=n['definitions'], md=v['max_demand'] * (2.0 if away else 1.0), dom=dom, ents=ents, n=n))
        caps = {}
        for cls in (True, False):
            cl = [r['md'] for r in recs if r['dom'] == cls and not any('val' in r['ents'].get(q, {}) for q in emb)]
            if cl: caps[cls] = collections.Counter(round(x, 3) for x in cl).most_common(1)[0][0]
        for r in recs:
            cap = caps.get(r['dom'])
            if not cap: continue
            ents = r['ents']
            pw = [q for q in emb if q in ents and ents[q].get('ship_power', 0) + ents[q].get('province_power', 0) > 0]
            if len(pw) != 1: continue
            q = pw[0]; P = ents[q].get('ship_power', 0) + ents[q].get('province_power', 0)
            red = 1 - r['md'] / cap
            if red < 0.02: continue
            S = sum(x.get('ship_power', 0) + x.get('province_power', 0) for x in ents.values())
            nh = sum(1 for x in ents.values() if x.get('has_capital'))
            D = 0.5 * P / red
            rows.append(dict(save=e['id'], tag=tag, q=q, node=r['node'], P=P, S=S, nh=nh, D=D, red=red, pmax=r['n'].get('p_pow'), nomerch=sum(1 for x in ents.values() if x.get('has_trader'))))
print(len(rows), 'single-embargoer rows with red>=2%')
dd = [(r['D'] - r['S']) for r in rows]
print('D - S: quantiles', [round(sorted(dd)[int(p*(len(dd)-1))],1) for p in (0,.1,.25,.5,.75,.9,1)])
print('D/S  : quantiles', [round(sorted(r['D']/r['S'] for r in rows)[int(p*(len(rows)-1))],3) for p in (0,.1,.25,.5,.75,.9,1)])
print('rows with |D-(S+5nh)| <= 3% of S:', sum(abs(r['D']-(r['S']+5*r['nh'])) <= 0.03*r['S'] for r in rows), ' |D-S|<=3%:', sum(abs(r['D']-r['S']) <= 0.03*r['S'] for r in rows))
for r in rows[:0]: pass
# same embargoer across several nodes of one save: implied efficiency k_e = red*(S+5nh)/P
grp = collections.defaultdict(list)
for r in rows: grp[(r['save'], r['tag'], r['q'])].append(r['red'] * (r['S'] + 5 * r['nh']) / r['P'])
sp = [(max(v)-min(v), len(v), k) for k, v in grp.items() if len(v) >= 3]
print('groups (save,embargoed,embargoer) >=3 nodes:', len(sp), 'median spread of implied k:', round(statistics.median(s for s,_,_ in sp),3), 'share with spread<0.03:', round(sum(s < 0.03 for s,_,_ in sp)/len(sp),3))
