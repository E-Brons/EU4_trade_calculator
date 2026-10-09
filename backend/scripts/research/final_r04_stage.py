"""R04 final, script 7: the project's own `transfers`, `retain_power`, `pull_power` stages over the whole manifest (status of calc.py)."""
import sys, time
sys.path.insert(0, ".")
from app.trade import corpus
rep = corpus.run_corpus(progress=lambda i: None)
tot = {}
bad = []
for sid, r in rep.reports.items():
    for st in ("transfers", "retain_power", "pull_power"):
        x = r.stages[st]
        a = tot.setdefault(st, [0, 0])
        a[0] += x.checks; a[1] += x.failures
        if x.failures: bad.append((sid, st, x.failures))
print("saves", len(rep.reports), "missing", rep.missing)
print(tot)
print(bad)
