"""Value/flow (2026-10-08): steer_weights outside 5 % under strength variants (monkeypatched identify_observed).
  identified : calc 0.2.2 (strength from `add` ranks, default = most common)
  equal      : every steerer 0.05 (= TRADE_ADDED_VALUE_MODIFER; weights proportional to effective power)
  equal+id>  : 0.05 unless the identified strength is clearly higher (> 0.06: a trade_steering bonus)
Run from backend/: .venv/bin/python scripts/research/value_steer_variants.py [max_saves]"""
from __future__ import annotations

import math
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import calc, corpus  # noqa: E402

lim = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
orig = calc.identify_observed
variants = {
    "identified": lambda o: o,
    "equal": lambda o: replace(o, steering_strength={t: 0.05 for t in o.steering_strength}, default_steering_strength=0.05),
    "equal+id>": lambda o: replace(o, steering_strength={t: (s if s > 0.06 else 0.05) for t, s in o.steering_strength.items()}, default_steering_strength=0.05),
}
res = Counter(); n = 0
for entry, world in corpus.iter_worlds(corpus.selected()):
    n += 1
    if n > lim:
        break
    base = orig(world)
    for name, f in variants.items():
        calc.identify_observed = lambda w, _o=f(base): _o
        try:
            pairs = calc.predict_stage("steer_weights", world)
        finally:
            calc.identify_observed = orig
        res[(name, "checks")] += len(pairs)
        res[(name, "outside 5%")] += sum(1 for p in pairs if math.isnan(p.predicted) or abs(p.predicted - p.recorded) > max(0.0011, 0.05 * abs(p.recorded)))
        res[(name, "exact 0.001")] += sum(1 for p in pairs if not math.isnan(p.predicted) and abs(p.predicted - p.recorded) <= 0.0011)
print("saves", min(n, lim))
for name in variants:
    print(f"{name:12s} checks {res[(name,'checks')]}  outside 5% {res[(name,'outside 5%')]}  exact {res[(name,'exact 0.001')]}")
