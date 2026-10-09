"""Verifier (independent): embargo presence test (R01 C-02 / R10 C-05) and per-class constancy (R01 C-01/C-03)."""
import sys, re, pickle, collections
sys.path.insert(0, 'scripts/research')
import common
TAG = re.compile(r'^[A-Z0-9]{2,4}$')
C = collections.Counter()
for e in common.entries():
    m = pickle.loads((common.CACHE / f"master_{e['id']}.pkl").read_bytes())
    nodes = m['nodes']
    for tag, c in m['countries'].items():
        emb = c.get('trade_embargoed_by') or []
        if not isinstance(emb, list): emb = [emb]
        home = c.get('home_node')
        rows = []  # (node, cls, md_adj, embargoer_own_total)
        for n in nodes:
            t = n.get(tag)
            if not isinstance(t, dict) or 'max_demand' not in t: continue
            top = n.get('top_provinces') or []
            cls = 'home' if (n['definitions'] == home or (top and top[0] == tag)) else 'foreign'
            away = ('total' in t) and not t.get('has_capital')
            md = t['max_demand'] * (2.0 if away else 1.0)
            own = sum(max(0.0, n[x].get('max_pow', 0.0) - n[x].get('prev', 0.0)) for x in emb if isinstance(n.get(x), dict))
            rows.append((n['definitions'], cls, round(md, 3), own, away))
        if not emb:
            # non-embargoed: distinct values per class, excluding away
            for cls in ('home', 'foreign'):
                vals = {r[2] for r in rows if r[1] == cls and not r[4]}
                if vals: C['ne %s groups' % cls] += 1; C['ne %s single-valued(+-0.002)' % cls] += (max(vals) - min(vals) <= 0.002)
            allv = {r[2] for r in rows if not r[4] and r[1] == 'foreign'}
            continue
        for cls in ('home', 'foreign'):
            clean = [r[2] for r in rows if r[1] == cls and not r[4] and r[3] == 0]
            if not clean: continue
            cap = collections.Counter(clean).most_common(1)[0][0]
            for r in rows:
                if r[1] != cls: continue
                reduced = r[2] < cap - 0.0015
                has = r[3] > 0
                C[('embargoed rows: embargoer power %s, reduced %s' % (has, reduced))] += 1
print('\n'.join('%s %s' % (v, k) for k, v in sorted(C.items(), key=str)))
