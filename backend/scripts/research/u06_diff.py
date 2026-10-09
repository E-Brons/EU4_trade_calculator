import sys, json
sys.path.insert(0, "scripts/research")
import u06_load as L
order = ["S79","S80","U03","U04","U05","U06"]
T = {s: L.tur(s) for s in order}
def short(v, n=160):
    s = json.dumps(v, default=str) if not isinstance(v, str) else v
    return s if len(s) <= n else s[:n] + "..."
skip = {"history","ledger","historic_stats_cache","inflation_history","flags","active_relations","decision_seed","colors","army","navy","estate","cb","ai","leader","country_missions","previous_monarch","heir","monarch","queen"}
a, b = sys.argv[1], sys.argv[2]
A, B = T[a], T[b]
keys = sorted(set(A) | set(B))
print(f"== {a} -> {b}: changed top-level keys of countries.TUR")
for k in keys:
    if A.get(k) != B.get(k):
        if k in ("history","ledger","historic_stats_cache","inflation_history","army","navy","decision_seed","active_relations","cb","ai","colors"): 
            print(" (big)", k); continue
        print(f" {k}: {short(A.get(k))}  ->  {short(B.get(k))}")
