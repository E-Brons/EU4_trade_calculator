"""R01: distribution of max_demand per country across nodes; is it constant for countries that are not embargoed, apart from home/away?"""
import sys, os, re, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
out = collections.Counter(); examples = []
allrows = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    C = m['countries']
    per = collections.defaultdict(list)   # tag -> [(node, md, entry)]
    for n in m['nodes']:
        for k, v in n.items():
            if TAG.match(k) and isinstance(v, dict) and 'max_demand' in v:
                per[k].append((n['definitions'], v['max_demand'], v))
    for tag, rows in per.items():
        if tag == 'PIR': continue
        c = C.get(tag, {})
        emb_by = c.get('trade_embargoed_by') or []
        home = c.get('home_node')
        for nid, md, v in rows:
            collecting = 'total' in v
            allrows.append((e['id'], tag, nid, md, bool(emb_by), nid == home, collecting, 'has_capital' in v, 'val' in v))
pickle.dump(allrows, open(common.CACHE / 'r01_mdrows.pkl', 'wb'))
print(len(allrows), 'country-node max_demand values')
# group: not embargoed, not home node, not collecting-away
by = collections.defaultdict(list)
for r in allrows:
    sid, tag, nid, md, emb, ishome, coll, hascap, hasval = r
    if emb or ishome or coll or hascap: continue
    by[(sid, tag)].append(md)
cnt = collections.Counter(len(set(v)) for v in by.values())
print('non-embargoed countries (per save) with N distinct max_demand values over their passive/foreign nodes:', sorted(cnt.items())[:10])
tot = sum(cnt.values()); print('countries', tot, 'single value:', cnt[1], round(cnt[1]/tot,4))
# what about their distinct values -- spread
sp = [max(v)-min(v) for v in by.values() if len(set(v))>1]
print('spread (max-min) among those with >1 value: n',len(sp),'median',sorted(sp)[len(sp)//2] if sp else None,'max',max(sp) if sp else None)
