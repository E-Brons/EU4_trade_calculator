"""R01 Q1 / R10 Q5-Q6: test the embargo reduction  r = 1 - md_adj/cap  against the forum formula  sum_e P_e/(S+5*NHome) * 0.5 * eff.
cap = md_adj at nodes of the same class (domestic/foreign) where no embargoer has power. md_adj = md (x2 if collecting away)."""
import sys, os, re, collections, pickle, statistics
sys.path.insert(0, os.path.dirname(__file__))
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
pts = []; stats = collections.Counter(); caps_bad = []
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    C = m['countries']
    for tag, c in C.items():
        emb = c.get('trade_embargoed_by')
        if not emb: continue
        home = c.get('home_node')
        recs = []
        for n in m['nodes']:
            v = n.get(tag)
            if not (isinstance(v, dict) and 'max_demand' in v): continue
            ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
            S = sum(x.get('ship_power', 0) + x.get('province_power', 0) for x in ents.values())
            nh = sum(1 for x in ents.values() if x.get('has_capital'))
            den = S + 5 * nh
            Xs = []
            for q in emb:
                x = ents.get(q)
                P = (x.get('ship_power', 0) + x.get('province_power', 0)) if x else 0.0
                Xs.append(P / den if den else 0.0)
            away = ('total' in v) and not v.get('has_capital') and nid_home_diff if False else (('total' in v) and not v.get('has_capital'))
            top = (n.get('top_provinces') or [None])[0] == tag
            dom = (n['definitions'] == home) or top
            md = v['max_demand'] * (2.0 if away else 1.0)
            recs.append(dict(node=n['definitions'], md=md, dom=dom, X=sum(Xs), Xs=Xs, emb=emb, away=away, raw=v['max_demand'], ents=ents))
        caps = {}
        for cls in (True, False):
            clean = [r['md'] for r in recs if r['dom'] == cls and r['X'] == 0]
            if clean:
                vals = collections.Counter(round(x, 3) for x in clean)
                caps[cls] = max(clean)
                if len(vals) > 1 and max(vals) - min(vals) > 0.0025: stats['class with non-constant clean md'] += 1
        for r in recs:
            cap = caps.get(r['dom'])
            if cap is None: stats['no clean cap'] += 1; continue
            pts.append((e['id'], tag, r['node'], r['dom'], r['away'], cap, r['md'], r['X'], len(r['emb']), sum(1 for x in r['Xs'] if x > 0)))
print(stats, len(pts), 'embargoed-country nodes with a clean cap')
clean = [p for p in pts if p[7] == 0]; emb = [p for p in pts if p[7] > 0]
print('X==0 (no embargoer power at node): md equals cap in', sum(abs(p[6]-p[5]) < 0.0025 for p in clean), 'of', len(clean), '(by construction for the cap node(s); the rest are the other nodes with X=0)')
# with X>0
red = [(1 - p[6]/p[5], p[7], p) for p in emb]
print('nodes with embargoer power:', len(emb), ' md < cap by >0.3%:', sum(r > 0.003 for r, _, _ in red), ' md == cap (|r|<=0.003):', sum(abs(r) <= 0.003 for r, _, _ in red), ' md > cap:', sum(r < -0.003 for r, _, _ in red))
# slope through origin of r on X
num = sum(r*x for r, x, _ in red); den = sum(x*x for _, x, _ in red)
k = num/den if den else None; print('LS slope r ~ k*X :', k)
ss_res = sum((r-k*x)**2 for r, x, _ in red); mean = sum(r for r, _, _ in red)/len(red); ss_tot = sum((r-mean)**2 for r, _, _ in red); print('R2 (about mean):', 1-ss_res/ss_tot)
# per-row relative error with k=0.5
errs = [abs(r - 0.5*x) for r, x, _ in red]; print('k=0.5: median abs err in r', statistics.median(errs), ' p90', sorted(errs)[int(.9*len(errs))], ' within 0.005:', sum(e < 0.005 for e in errs), 'of', len(errs))
pickle.dump(pts, open(common.CACHE / 'r01_embargo_pts.pkl', 'wb'))
