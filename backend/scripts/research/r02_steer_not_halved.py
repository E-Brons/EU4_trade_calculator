"""R02 Q2: ratio md / same-class cap for entries by role (non-embargoed countries). cap = most common md of the country at same-class nodes where it has no merchant and no `total`."""
import sys, os, collections, pickle
sys.path.insert(0, os.path.dirname(__file__))
import common
rows = pickle.loads((common.CACHE / 'r01_rows2.pkl').read_bytes())
by = collections.defaultdict(list)
for r in rows: by[(r['save'], r['tag'])].append(r)
def role(r):
    v = r['v']
    if r['cap']: return 'home(has_capital)'
    if 'total' in v: return 'collect-away'
    if 'type' in v: return 'steer-away'
    if v.get('has_trader'): return 'merchant, no action'
    return 'no merchant (passive power/stub)'
res = collections.defaultdict(collections.Counter); ex = collections.defaultdict(list)
for k, rs in by.items():
    if any(r['emb'] for r in rs): continue
    caps = {}
    for dom in (True, False):
        cl = [r['md'] for r in rs if (r['ishome'] or r['top']) == dom and role(r) in ('no merchant (passive power/stub)',)]
        if cl: caps[dom] = collections.Counter(cl).most_common(1)[0][0]
    for r in rs:
        dom = r['ishome'] or r['top']; cap = caps.get(dom)
        if cap is None or r['ishome']: continue
        q = r['md'] / cap
        rl = role(r)
        res[rl]['n'] += 1
        res[rl]['ratio==1 (±0.0015 abs md)' if abs(r['md'] - cap) <= 0.0015 else ('ratio==0.5' if abs(r['md'] - 0.5 * cap) <= 0.0015 else 'other')] += 1
        if abs(r['md'] - cap) > 0.0015 and abs(r['md'] - 0.5 * cap) > 0.0015 and len(ex[rl]) < 4: ex[rl].append((k, r['node'], r['md'], cap))
for rl, c in res.items(): print(rl, dict(c))
print(dict(ex))
