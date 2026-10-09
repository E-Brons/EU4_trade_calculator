"""Verifier (independent): TUR S79 per-row embargo table of R01 response (observed reduction vs 0.5*sum own_e/(sum own + 5*NH))."""
import sys, pickle, collections, re
sys.path.insert(0, 'scripts/research')
import common
TAGRE = re.compile(r'^[A-Z0-9]{2,4}$')
sid, me = sys.argv[1] if len(sys.argv) > 1 else 'S79', sys.argv[2] if len(sys.argv) > 2 else 'TUR'
m = pickle.loads((common.CACHE / f"master_{sid}.pkl").read_bytes())
c = m['countries'][me]; emb = c['trade_embargoed_by']; home = c['home_node']
nh = collections.Counter(cc.get('home_node') for cc in m['countries'].values())
rows = []
for n in m['nodes']:
    t = n.get(me)
    if not isinstance(t, dict) or 'max_demand' not in t: continue
    top = n.get('top_provinces') or []
    cls = 'dom' if (n['definitions'] == home or (top and top[0] == me)) else 'for'
    away = 'total' in t and not t.get('has_capital')
    own = {x: n[x].get('max_pow', 0) - n[x].get('prev', 0) for x in emb if isinstance(n.get(x), dict) and 'max_pow' in n[x]}
    tot = sum((v.get('max_pow', 0) - v.get('prev', 0)) for k, v in n.items() if TAGRE.match(k) and isinstance(v, dict) and 'max_pow' in v)
    rows.append([n['definitions'], cls, away, t['max_demand'], own, tot, sum(1 for k, v in n.items() if TAGRE.match(k) and isinstance(v, dict) and v.get('has_capital'))])
cap = {}
for cls in ('dom', 'for'):
    cl = [r[3] for r in rows if r[1] == cls and not r[2] and not any(v > 0 for v in r[4].values())]
    cap[cls] = collections.Counter(cl).most_common(1)[0][0] if cl else None
print('caps', cap)
for nid, cls, away, md, own, tot, NH in rows:
    if not any(v > 0 for v in own.values()) and md >= (cap[cls] or 9) * (0.5 if away else 1) - 0.0015: continue
    if cap[cls] is None: print(nid, cls, 'no clean cap', md); continue
    capx = cap[cls] * (0.5 if away else 1)
    obs = 100 * (1 - md / capx)
    pred = 100 * sum(0.5 * v for v in own.values()) / (tot + 5 * NH) if tot + 5 * NH else 0
    print('%-18s %s%s md=%.3f cap=%.3f obs=%.2f pred=%.2f %s' % (nid, cls, '/away' if away else '', md, capx, obs, pred, {k: round(v, 1) for k, v in own.items() if v}))
