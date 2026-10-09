"""R01 home bonus on the new saves: for every country with a home entry and a top-province (non-home, idle) node, print md difference, #steering merchants, away collector, embargo."""
import sys, collections; sys.path.insert(0, 'scripts/research')
import u345_home_load as L
def f(x, d=None):
    try: return float(x)
    except Exception: return d
for sid in sys.argv[1:] or ['U03', 'U04', 'U05']:
    ns = L.nodes(sid); cs = L.countries(sid); ents = collections.defaultdict(list)
    for n in ns:
        for tag, e in n.items():
            if isinstance(e, dict) and len(tag) <= 4 and 'max_demand' in e and tag.upper() == tag or (isinstance(e, dict) and tag[:1] == 'C' and tag[1:].isdigit()):
                ents[tag].append((n, e))
    print("==", sid, "(countries with a steering merchant and a home entry)")
    for tag, lst in sorted(ents.items()):
        home = [e for n, e in lst if 'has_capital' in e]
        k = sum(1 for n, e in lst if 'type' in e and e.get('has_trader'))
        if not home or k == 0: continue
        tops = [e for n, e in lst if (n.get('top_provinces') or [None])[0] == tag and 'has_capital' not in e and 'total' not in e and 'type' not in e and not e.get('has_trader')]
        away = any('total' in e and 'has_capital' not in e for n, e in lst)
        emb = bool((cs.get(tag) or {}).get('trade_embargoed_by'))
        d = round(f(home[0]['max_demand']) - f(tops[0]['max_demand']), 3) if tops else None
        print(f"  {tag:4s} k={k} away_collector={away!s:5} embargoed={emb!s:5} home_md={home[0]['max_demand']} top_md={tops[0]['max_demand'] if tops else None} diff={d}  0.1k={round(.1*k,1)}")
