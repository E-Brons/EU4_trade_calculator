"""R01 Q1 refinement: which embargoer power measure and denominator reproduce the reduction exactly?"""
import sys, os, re, collections, pickle, statistics, itertools
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
data = []   # one per (save, country, node) with caps
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    C = m['countries']
    for tag, c in C.items():
        emb = c.get('trade_embargoed_by')
        if not emb: continue
        home = c.get('home_node'); recs = []
        for n in m['nodes']:
            v = n.get(tag)
            if not (isinstance(v, dict) and 'max_demand' in v): continue
            ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
            away = ('total' in v) and not v.get('has_capital')
            dom = (n['definitions'] == home) or ((n.get('top_provinces') or [None])[0] == tag)
            recs.append(dict(node=n['definitions'], md=v['max_demand'] * (2.0 if away else 1.0), dom=dom, ents=ents))
        # clean cap: nodes where no embargoer has any entry with val
        caps = {}
        for cls in (True, False):
            cl = [r['md'] for r in recs if r['dom'] == cls and not any('val' in r['ents'].get(q, {}) for q in emb)]
            if cl: caps[cls] = collections.Counter(round(x, 3) for x in cl).most_common(1)[0][0]
        for r in recs:
            cap = caps.get(r['dom'])
            if cap: data.append(dict(save=e['id'], tag=tag, emb=emb, cap=cap, **r))
print(len(data), 'rows')
# case A: embargoers with val>0 only through prev (no province/ship): does md fall?
c = collections.Counter()
for d in data:
    pw = [q for q in d['emb'] if d['ents'].get(q, {}).get('ship_power', 0) + d['ents'].get(q, {}).get('province_power', 0) > 0]
    vw = [q for q in d['emb'] if 'val' in d['ents'].get(q, {})]
    red = 1 - d['md'] / d['cap']
    if not pw and vw: c[('embargoer present only by prev/extras', 'reduced' if red > 0.003 else 'not reduced')] += 1
    if not pw and not vw: c[('no embargoer entry with val', 'reduced' if red > 0.003 else 'not reduced')] += 1
    if pw: c[('embargoer has province/ship power', 'reduced' if red > 0.003 else 'not reduced')] += 1
for k, v in sorted(c.items()): print(k, v)
# single embargoer with power: ratio r/X by variant
def own(x): return x.get('max_pow',0) - x.get('prev',0)
variants = {
 'own/(Sown+5NH)': lambda ents, q: own(ents[q])/(sum(own(x) for x in ents.values())+5*sum(1 for x in ents.values() if x.get('has_capital'))),
 'own/Sown': lambda ents, q: own(ents[q])/sum(own(x) for x in ents.values()),
 'own/(Sown+5NH) wo capital extras': lambda ents, q: own(ents[q])/(sum(own(x) for x in ents.values())),
 'P/(S+5NH)':   lambda ents, q: (lambda S, nh: (ents[q].get('ship_power',0)+ents[q].get('province_power',0))/(S+5*nh))(sum(x.get('ship_power',0)+x.get('province_power',0) for x in ents.values()), sum(1 for x in ents.values() if x.get('has_capital'))),
 'P/S':         lambda ents, q: (ents[q].get('ship_power',0)+ents[q].get('province_power',0))/sum(x.get('ship_power',0)+x.get('province_power',0) for x in ents.values()),
 'val/total':   lambda ents, q: ents[q].get('val',0)/sum(x.get('val',0) for x in ents.values()),
 'maxpow/sum':  lambda ents, q: ents[q].get('max_pow',0)/sum(x.get('max_pow',0) for x in ents.values()),
 'prov/sumprov':lambda ents, q: ents[q].get('province_power',0)/sum(x.get('province_power',0) for x in ents.values()),
}
single = []; single2 = []
for d in data:
    pw = [q for q in d['emb'] if q in d['ents'] and d['ents'][q].get('ship_power', 0) + d['ents'][q].get('province_power', 0) > 0]
    if len(pw) == 1: single.append((d, pw[0]))
    pw2 = [q for q in d['emb'] if q in d['ents'] and own(d['ents'][q]) > 0]
    if len(pw2) == 1 and len(pw) != 1: single2.append((d, pw2[0]))
print('single-embargoer rows', len(single))
for name, f in variants.items():
    grp = collections.defaultdict(list)
    for d, q in single:
        try: X = f(d['ents'], q)
        except ZeroDivisionError: continue
        if X > 0.001: grp[(d['save'], q)].append((1 - d['md'] / d['cap']) / X)
    spreads = [ (max(v) - min(v)) for v in grp.values() if len(v) >= 3]
    med = statistics.median([statistics.median(v) for v in grp.values()])
    print(name, 'groups(save,embargoer) with >=3 nodes:', len(spreads), ' median within-group spread of r/X:', round(statistics.median(spreads), 4), ' median ratio', round(med, 3))
