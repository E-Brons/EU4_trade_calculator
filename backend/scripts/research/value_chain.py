"""Value/flow (2026-10-08): first divergence of the end-to-end chain per save, grouped by cause.
Run from backend/: .venv/bin/python scripts/research/value_chain.py
For each clean save: calc.calculate from raw inputs; walk the nodes in topological order and find the first node
whose computed value (gross, retention, current, entry val/max_pow, link values) leaves 5 % of the recorded one."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import calc, corpus, game_data  # noqa: E402
from app.trade.calc import UnknownVariable  # noqa: E402


def off(p, r, a=0.0011, rel=0.05):
    return abs(p - r) > max(a, rel * abs(r))


def main(only=None):
    g = game_data.graph()
    causes = Counter(); rows = []
    for entry, world in corpus.iter_worlds(corpus.selected()):
        if only and entry["id"] not in only:
            continue
        obs = calc.identify_observed(world)
        try:
            res = calc.calculate(world.inputs, world.inputs.decisions, obs)
        except UnknownVariable as e:
            causes["unknown:" + str(e).split(":")[0][:40]] += 1
            rows.append((entry["id"], "unknown", str(e)[:120])); continue
        rec = world.recorded
        first = None
        for node in g.topo_order():
            nr, cr = rec.nodes.get(node), res.nodes.get(node)
            if nr is None or cr is None:
                continue
            # entry-level first: power and val
            ent_bad = []
            for (n, tag), r in rec.entries.items():
                if n != node or (n, tag) not in res.entries:
                    continue
                c = res.entries[(n, tag)]
                if r.max_pow is not None and off(c.max_pow, r.max_pow):
                    ent_bad.append(("max_pow", tag, round(c.max_pow, 3), r.max_pow))
                elif r.val is not None and off(c.val, r.val):
                    ent_bad.append(("val", tag, round(c.val, 3), r.val))
            gross_rec = world.inputs.nodes[node].local_value + sum(v for _s, v, _a in nr.incoming)
            checks = []
            if ent_bad:
                checks.append(("entry " + ent_bad[0][0], ent_bad[:3]))
            if nr.retention is not None and off(cr.retention, nr.retention, 0.0011, 0.02):
                checks.append(("retention", (round(cr.retention, 3), nr.retention)))
            if off(cr.gross, gross_rec):
                checks.append(("gross(incoming)", (round(cr.gross, 3), round(gross_rec, 3))))
            if nr.current is not None and off(cr.current, nr.current):
                checks.append(("current", (round(cr.current, 3), nr.current)))
            if checks:
                first = (node, checks); break
        if first is None:
            causes["ok (no node off)"] += 1; rows.append((entry["id"], "ok", "")); continue
        node, checks = first
        causes[checks[0][0]] += 1
        rows.append((entry["id"], node, json.dumps(checks)[:300]))
    print(dict(causes))
    for r in rows:
        print(*r)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
