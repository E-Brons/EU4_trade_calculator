"""Value/flow (2026-10-08): end-to-end chain on all clean saves with the two proposed calc changes:
  P1 trade efficiency: identified at any collecting entry with money; 0.0 for countries with no recorded money anywhere
  P2 val clipped at 0 (entries with negative max_pow store no val: 109 of 109)
Reports chain completion, player income within the chain tolerance, node `current` within it.
Run from backend/: .venv/bin/python scripts/research/value_chain_proposed.py [p1] [p2]"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.trade import calc, corpus, verify  # noqa: E402

args = set(sys.argv[1:]) or {"p1", "p2"}
orig_val = calc.rule_val
if "p2" in args:
    calc.rule_val = lambda mp, m: max(0.0, orig_val(mp, m))
if "p1" in args:
    import value_efficiency_gap as veg  # noqa: E402  (defines proposed_observed)
    get_obs = veg.proposed_observed
else:
    get_obs = calc.identify_observed
st = Counter()
for entry, world in corpus.iter_worlds(corpus.selected()):
    try:
        res = calc.calculate(world.inputs, world.inputs.decisions, get_obs(world))
    except calc.UnknownVariable:
        st["unknown"] += 1; continue
    st["complete"] += 1
    for n, nr in world.recorded.nodes.items():
        if nr.current is not None and n in res.nodes:
            st["node checks"] += 1; st["node current off"] += not verify.close(res.nodes[n].current, nr.current, *verify.CHAIN_TOLERANCE)
    rec = sum(r.money or 0 for (n, t), r in world.recorded.entries.items() if t == world.inputs.player)
    st["player income ok"] += verify.close(res.income(world.inputs.player), rec, *verify.CHAIN_TOLERANCE)
print(sorted(args), dict(st))
