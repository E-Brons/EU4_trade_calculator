import sys, statistics as st
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import u06_load as L
def f(x, d=None):
    try: return float(x)
    except (TypeError, ValueError): return d
def table(s):
    out = {}
    for n in L.nodes(s):
        for tag, e in n.items():
            if isinstance(e, dict) and "max_demand" in e and len(tag) <= 4 and tag.isupper():
                out[(n["definitions"], tag)] = e
    return out
A, B = table(sys.argv[1]), table(sys.argv[2])
common = [k for k in A if k in B]
print(sys.argv[1], "->", sys.argv[2], "pairs with max_demand in both:", len(common))
# per-country constant? ratio per country (median over nodes) 
byc = defaultdict(list)
for (nd, tag) in common:
    a, b = f(A[(nd, tag)]["max_demand"]), f(B[(nd, tag)]["max_demand"])
    if a and b: byc[tag].append(b / a)
med = {t: st.median(v) for t, v in byc.items()}
allr = [r for v in byc.values() for r in v]
print("overall ratio median %.4f  p10 %.4f  p90 %.4f" % (st.median(allr), sorted(allr)[len(allr)//10], sorted(allr)[9*len(allr)//10]))
print("share of pairs with |ratio-1|<0.0015:", round(sum(abs(r-1) < 0.0015 for r in allr)/len(allr), 4), "of", len(allr))
print("country medians: #countries", len(med), "Counter of rounded median ratio (3 dec), top:", Counter(round(m, 3) for m in med.values()).most_common(6))
print("TUR median ratio %.4f" % med["TUR"])
tur = sorted(((nd, round(f(B[(nd,'TUR')]['max_demand'])/f(A[(nd,'TUR')]['max_demand']), 4), f(A[(nd,'TUR')]['max_demand']), f(B[(nd,'TUR')]['max_demand']))
              for nd in {k[0] for k in common if k[1] == 'TUR'}), key=lambda x: x[1])
print("TUR per node ratio:", [(n, r) for n, r, a, b in tur][:4], "...", [(n, r) for n, r, a, b in tur][-4:])
print("TUR nodes with ratio within 0.0015 of 1:", sum(abs(r-1) < 0.0015 for n, r, a, b in tur), "of", len(tur))
