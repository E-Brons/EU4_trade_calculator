"""R04 final, script 8: potential stubs (node without `total`) and the range of giver val."""
import sys
from collections import Counter
sys.path.insert(0, "scripts/research")
import final_r04_common as F
saves = []; mx = 0; other_nototal = Counter()
for sid, e, nodes in F.saves():
    for n in nodes:
        if "total" not in n:
            k = sum(1 for t, c in F.entries_of(n).items() if "potential" in c)
            if k: saves.append((sid, n["definitions"], k))
            other_nototal[n["definitions"]] += 1
        for t, c in F.entries_of(n).items():
            if "t_out" in c: mx = max(mx, F.m(c["val"]))
print("nodes without total having potential entries:", len(saves), "saves", sorted({s[0] for s in saves})[:3], "...", sorted({s[0] for s in saves})[-1], Counter(s[1] for s in saves), Counter(s[2] for s in saves))
print("nodes without total (any), by node:", other_nototal)
print("max giver val", mx)
