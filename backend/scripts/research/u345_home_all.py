"""Q3: R06 / R07 / R02 / R01 headline tests over ALL countries of S79,S80 (reference) and U03,U04,U05 (own code)."""
import sys, collections; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
from statistics import mode
def f(x, d=None):
    try: return float(x)
    except Exception: return d
def mods(e):
    m = e.get('modifier')
    return [] if m is None else (m if isinstance(m, list) else [m])
SAVES = sys.argv[1:] or L.IDS
TOL = 0.0015
for sid in SAVES:
    ns = L.nodes(sid); cs = L.countries(sid)
    ents = collections.defaultdict(list)   # tag -> [(node dict, entry)]
    for n in ns:
        for tag, e in n.items():
            if isinstance(e, dict) and (tag.isupper() or tag[0] in 'CD') and len(tag) <= 4 and 'max_demand' in e:
                ents[tag].append((n, e))
    # ---- R06: residual R per merchant country
    Rc = {}; bad = 0; tot = 0; nohat = 0
    for tag, lst in ents.items():
        Rs = set()
        for n, e in lst:
            if 'max_pow' not in e: continue
            ext = f(e['max_pow']) - f(e.get('province_power'), 0) - f(e.get('ship_power'), 0) - f(e.get('prev'), 0)
            R = round(ext - 5 * ('has_capital' in e) - sum(f(m.get('power'), 0) for m in mods(e)), 3)
            if e.get('has_trader'): Rs.add(R)
            elif abs(R) > 0.0015: nohat += 1
        if Rs: Rc[tag] = Rs
    ok = multi = pred_fail = 0; fails = []
    for tag, Rs in Rc.items():
        c = cs.get(tag) or {}
        reforms = set(((c.get('government') or {}).get('reform_stack') or {}).get('reforms') or [])
        ideas = c.get('active_idea_groups') or {}
        pred = 2 + 5 * bool(reforms & {'mercantilistic_approach_reform', 'pious_merchants_reform'}) + 15 * (f(ideas.get('trade_ideas'), 0) >= 5)
        if len(Rs) > 1: multi += 1
        if Rs == {float(pred)}: ok += 1
        else: fails.append((tag, sorted(Rs), pred))
    print(f"[{sid}] R06: merchant countries {len(Rc)}; R==2+5a+15b: {ok}; multi-valued {multi}; failures {len(fails)} {fails[:6]}; entries w/o has_trader but R!=0: {nohat}")
    # ---- R07: X home vs away per country
    cnt = collections.Counter(); exc = []
    for tag, lst in ents.items():
        home = [(n, e) for n, e in lst if 'has_capital' in e and 'total' in e and f(e['total'], 0) >= 3]
        away = [(n, e) for n, e in lst if 'has_capital' not in e and 'total' in e and f(e['total'], 0) >= 3]
        if not home or not away: continue
        h = home[0][1]; Xh = f(h['money']) / f(h['total']) - 1; hm = bool(h.get('has_trader'))
        for n, e in away:
            Xa = f(e['money']) / f(e['total']) - 1
            d = round(Xa - Xh, 2)
            cnt[('home merchant' if hm else 'home no merchant', 'away merchant' if e.get('has_trader') else 'away no merchant', d)] += 1
    print(f"[{sid}] R07 away X - home X:", dict(cnt))
    # ---- R02: away-collecting md vs 0.5 * passive-value
    ar = collections.Counter(); aex = []
    for tag, lst in ents.items():
        pv = sorted({round(f(e['max_demand']), 3) for n, e in lst if not e.get('has_trader') and 'total' not in e and 'has_capital' not in e and 'type' not in e})
        for n, e in lst:
            if 'total' in e and 'has_capital' not in e:
                md = f(e['max_demand'])
                hit = [v for v in pv if abs(md - 0.5 * v) <= TOL + 0.0005]
                emb = bool((cs.get(tag) or {}).get('trade_embargoed_by'))
                ar[('0.5 x some passive value' if hit else 'NO match', 'embargoed tag' if emb else 'not embargoed')] += 1
                if not hit: aex.append((tag, n['definitions'], md, pv[:4]))
    print(f"[{sid}] R02 away collectors:", dict(ar), "non-matching:", aex[:8])
    # steering/idle not halved: md of steering entry equals some passive value (within tol)
    sr = collections.Counter()
    for tag, lst in ents.items():
        pv = sorted({round(f(e['max_demand']), 3) for n, e in lst if not e.get('has_trader') and 'total' not in e and 'has_capital' not in e and 'type' not in e})
        for n, e in lst:
            if 'type' in e and 'total' not in e and 'has_capital' not in e and pv:
                md = f(e['max_demand']); sr['steer md ~ a passive value' if any(abs(md - v) <= 0.003 for v in pv) else 'steer md differs'] += 1
    print(f"[{sid}] R02 steering-away:", dict(sr))
    # ---- R01 home bonus: home md - top-province-node md vs 0.1 * steering merchants
    hb = []
    for tag, lst in ents.items():
        home = [e for n, e in lst if 'has_capital' in e]
        tops = [e for n, e in lst if (n.get('top_provinces') or [None])[0] == tag and 'has_capital' not in e and 'total' not in e and 'type' not in e and not e.get('has_trader')]
        if not home or not tops: continue
        k = sum(1 for n, e in lst if 'type' in e and e.get('has_trader'))
        away = any('total' in e and 'has_capital' not in e for n, e in lst)
        d = round(f(home[0]['max_demand']) - f(tops[0]['max_demand']), 3)
        emb = bool((cs.get(tag) or {}).get('trade_embargoed_by'))
        hb.append((tag, d, k, away, emb))
    nb = [h for h in hb if not h[4]]
    print(f"[{sid}] R01 home bonus: countries {len(hb)} (non-embargoed {len(nb)}); with k>=1 steering & no away: ", [(h[0], h[1], h[2]) for h in nb if h[2] >= 1 and not h[3]][:12], "| with away collector: diff values", collections.Counter(h[1] for h in nb if h[3]).most_common(3))
