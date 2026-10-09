"""Modal dX by dip-level step (adm unchanged) and by adm-level step (dip unchanged), pooled over consecutive saves.
Unit-step cases only; entries must be collecting in both saves with the same has_trader/has_capital flags."""
import sys
from collections import Counter, defaultdict
sys.path.insert(0, "scripts/research")
import u06_load as L
from u06_dx_tech import entries, techs, order  # reuses loaders (prints its own tables once)
by_dip, by_adm = defaultdict(Counter), defaultdict(Counter)
for a, b in zip(order, order[1:]):
    EA, EB, TA, TB = entries(a), entries(b), techs(a), techs(b)
    for k in EA:
        if k not in EB or EA[k][1:] != EB[k][1:]: continue
        tag = k[1]
        if tag not in TA or tag not in TB: continue
        A, B = TA[tag], TB[tag]
        dx = round(EB[k][0] - EA[k][0], 2)
        dadm, ddip = B.get("adm_tech", 0) - A.get("adm_tech", 0), B.get("dip_tech", 0) - A.get("dip_tech", 0)
        if dadm == 0 and ddip == 1: by_dip[(A["dip_tech"], B["dip_tech"])][dx] += 1
        if ddip == 0 and dadm == 1: by_adm[(A["adm_tech"], B["adm_tech"])][dx] += 1
print("dip step (adm unchanged): level -> dX counter")
for k in sorted(by_dip): print(" ", k, sum(by_dip[k].values()), dict(by_dip[k].most_common(5)))
print("adm step (dip unchanged): level -> dX counter")
for k in sorted(by_adm): print(" ", k, sum(by_adm[k].values()), dict(by_adm[k].most_common(5)))
