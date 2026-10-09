"""Value/flow (2026-10-08): entries with negative max_pow (e.g. after merchant_recalled -10) record no `val`; the game
counts them as 0 power. Test: rule_val clipped at 0, on the stages pull_power, retain_power, current_value, val.
Run from backend/: .venv/bin/python scripts/research/value_negative_val.py [max_saves]"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import calc, corpus, verify  # noqa: E402

lim = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
orig = calc.rule_val
neg = Counter(); out = Counter(); n = 0
for entry, world in corpus.iter_worlds(corpus.selected()):
    n += 1
    if n > lim:
        break
    for (node, tag), r in world.recorded.entries.items():
        if r.max_pow is not None and r.max_pow < 0:
            neg["entries max_pow<0"] += 1; neg["of them val recorded"] += r.val is not None
    for name, fn in (("0.2.2", orig), ("clip>=0", lambda mp, m: max(0.0, orig(mp, m)))):
        calc.rule_val = fn
        try:
            rep = verify.verify_world(world, stages=("val", "retain_power", "pull_power", "current_value"), with_chain=False)
        finally:
            calc.rule_val = orig
        for st in rep.stages.values():
            out[(name, st.stage, "exact-fail")] += st.failures
            out[(name, st.stage, "outside5%")] += st.margin_failures
print("saves", min(n, lim), dict(neg))
for k in sorted(out):
    print(k, out[k])
