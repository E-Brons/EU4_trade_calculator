"""R12 final, script 2: link bookkeeping and the explanation of the mismatch  sum(downstream incoming.value) != outgoing.
Exact integer thousandths (m3). Whole corpus (84 distinct saves). Run from backend/.
  L1 every outgoing link L (graph edge order) has exactly one incoming record at its target (from = 1-based source index)
  L2 incoming.value - incoming.add == floor( outgoing * w_L )           w_L = steer_power[L] (3-decimal), floor at 3 decimals
  L3 incoming.add == floor( floor(outgoing*w_L) * A_L ),  A_L = sum of country `add` of the entries whose steer_power index == L
  L4 node identity  sum(value) - outgoing == sum(add) + [ sum_L floor(outgoing*w_L) - outgoing ]  and the bracket is in (-(outgoing*(1-sum w)) - links, 0]
  L5 rates of  |sum(value) - outgoing|  at several tolerances, and the cause of every node with sum(value) != outgoing"""
import sys
sys.path.insert(0, "scripts/research")
from collections import Counter, defaultdict
from final_r12_common import *

c = Counter(); ex = defaultdict(list)
wsums = Counter()
rows = []     # per node with outgoing key: (sid, nid, d, sumadd, sumw, k, out)
for sid, date, kind, nodes in saves(distinct=True):
    inc = incoming_links(nodes)
    for n in nodes:
        nid = n["definitions"]
        if not OUT[nid]: continue
        o = m3(n.get("outgoing", 0)); w = [m3(x) for x in lst(n.get("steer_power"))]
        c["nodes with links"] += 1
        if len(w) != len(OUT[nid]): ex["L0 steer_power length"].append((sid, nid))
        ents = entries_of(n)
        sv = sa = sfl = 0
        for i, (t, wi) in enumerate(zip(OUT[nid], w)):
            L = inc.get((nid, t), [])
            c["links"] += 1
            if len(L) != 1:
                ex["L1 one incoming record per link"].append((sid, nid, t, len(L))); continue
            c["L1 ok"] += 1
            v, a = L[0]; base = (o * wi) // 1000
            sv += v; sa += a; sfl += base
            if v - a == base: c["L2 ok"] += 1
            else: ex["L2"].append((sid, nid, t, o, wi, v, a))
            if a > 0: c["links with add > 0"] += 1
            A = sum(m3(e["add"]) for e in ents.values() if "add" in e and (int(e["steer_power"]) if e.get("steer_power") is not None else 0) == i)
            if a == (base * A) // 1000: c["L3 ok"] += 1
            else: ex["L3"].append((sid, nid, t, "outgoing", o, "w", wi, "A", A, "recorded add", a, "floor(base*A)", (base * A) // 1000))
        sw = sum(w); k = len(w)
        wsums[sw] += 1
        d = sv - o
        # L4: d - sa = sfl - o ; bracket upper bound 0, lower bound -(o*(1000-sw)/1000) - k   (strict)
        br = sfl - o
        lo = -(o * (1000 - sw)) / 1000 - k
        if br <= 0 and br > lo - 1e-9 and (d - sa) == br: c["L4 ok"] += 1
        else: ex["L4"].append((sid, nid, br, lo))
        if "outgoing" in n: rows.append((sid, nid, d, sa, sw, k, o))
print("counts", dict(c)); print("steer_power sums over all nodes with links:", dict(sorted(wsums.items())))
for k, v in ex.items(): print("EXCEPTIONS", k, len(v), v[:10])

# L5: rates on nodes that carry `outgoing` (5,923) and the cause classification
tot = len(rows); print("\nnodes with `outgoing` key:", tot, " distinct (sid-independent) node-instances; U01/U02 excluded")
def rate(f): return sum(1 for r in rows if f(r))
print("sum(value) == outgoing exactly:", rate(lambda r: r[2] == 0))
for tol in (1, 2, 5, 10, 50):
    print(f"|d| <= {tol/1000:.3f}:", rate(lambda r, tol=tol: abs(r[2]) <= tol))
print("|d| <= 0.0015 x links:", rate(lambda r: abs(r[2]) <= 1.5 * r[5]))
print("|d| <= 0.5% of outgoing:", rate(lambda r: abs(r[2]) * 200 <= r[6]), " <= 1%:", rate(lambda r: abs(r[2]) * 100 <= r[6]), " <= 2%:", rate(lambda r: abs(r[2]) * 50 <= r[6]))
print("|d - sum(add)| <= 0.0015 x links (bookkeeping without add):", rate(lambda r: abs(r[2] - r[3]) <= 1.5 * r[5]))
cls = Counter()
for sid, nid, d, sa, sw, k, o in rows:
    key = ("add>0" if sa > 0 else "add=0", "sum w<1.000" if sw < 1000 else "sum w=1.000", "d==0" if d == 0 else ("d>0" if d > 0 else "d<0"))
    cls[key] += 1
print("\ncause table (add, weight sum, sign of d):")
for k, v in sorted(cls.items()): print("  ", k, v)
# nodes with d != 0 and no add and sum w = 1.000: only per-link flooring
fl = [r for r in rows if r[2] != 0 and r[3] == 0 and r[4] == 1000]
print("d != 0, no add, sum w = 1.000 (flooring only):", len(fl), " max |d| (m3):", max(abs(r[2]) for r in fl), " max links:", max(r[5] for r in fl))
mx = max(rows, key=lambda r: r[2]); print("largest d > 0:", mx)
print("largest |d| with add = 0:", max((r for r in rows if r[3] == 0), key=lambda r: abs(r[2])))
print("sum(value) - sum(add) > outgoing in any node:", rate(lambda r: r[2] - r[3] > 0))
first80 = [r for r in rows if r[0].startswith("S")]
print("S01-S80 only: nodes with outgoing", len(first80), " max d (ducats)", max(r[2] for r in first80) / 1000, " exact", sum(1 for r in first80 if r[2] == 0),
      " |d|<=0.01:", sum(1 for r in first80 if abs(r[2]) <= 10), " |d|<=0.0015 x links:", sum(1 for r in first80 if abs(r[2]) <= 1.5 * r[5]))
