"""R11 final (5/5): status of app/trade/calc.py for ships. Runs the project's raw_power stage on the ticked saves and splits the
failures by 'entry has ships' / 'entry has no ships'. (Uses app.trade.calc on purpose: this script reports the implementation status,
it is not a verification of the rule.)"""
import sys, os
sys.path.insert(0, ".")
from app.trade import corpus, calc
from collections import Counter

ids = ["S79", "S80", "U03", "U04", "U05", "U06"]
tot = Counter()
for entry, world in corpus.iter_worlds([e for e in corpus.manifest() if e["id"] in ids]):
    pairs = calc.predict_stage("raw_power", world)
    for p in pairs:
        e = world.inputs.entries[(p.node, p.tag)]
        ships = e.light_ships > 0
        ok = abs(p.predicted - p.recorded) <= max(0.0105, 1e-4 * abs(p.recorded))
        tot[("ships" if ships else "noships", "ok" if ok else "fail")] += 1
        if ships and not ok: print("  ship entry FAIL", entry["id"], p.tag, p.node, round(p.predicted, 3), p.recorded)
    print(entry["id"], dict(tot), flush=True)
print(dict(tot))
