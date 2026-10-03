"""Debug helper: node-by-node comparison of the simulator against a real
save's own numbers, sorted by error size -- for investigating a failure in
tests/test_real_saves.py.

Usage:
    python3 scripts/compare_save.py path/to/Save.eu4

Example against a fixture save from tests/fixtures/saves/:
    python3 scripts/compare_save.py tests/fixtures/saves/S14_TUR_1444.11.11.eu4
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engine.model import Allocation, Params
from app.engine.simulate import simulate
from app.parsing.save import build_node_states_from_save, load_save
from app.parsing.tradenodes import load_trade_graph


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    save_path = Path(sys.argv[1])

    graph = load_trade_graph()
    parsed = load_save(save_path)
    print(f"player_tag = {parsed.player_tag}")
    for w in parsed.warnings:
        print(f"warning: {w}")

    node_states, current_allocation, home_node, _real_presence = build_node_states_from_save(parsed, graph)
    print(f"home_node = {home_node}")
    print(f"suggested_trade_efficiency = {parsed.suggested_trade_efficiency}")
    print(f"actual_current_income (save) = {parsed.actual_current_income:.3f}")

    if parsed.suggested_trade_efficiency is None:
        print("No collecting node to back-solve trade efficiency from -- nothing to simulate.")
        return

    params = Params(trade_efficiency=parsed.suggested_trade_efficiency)
    result = simulate(graph, node_states, Allocation(nodes=dict(current_allocation)), params)
    print(f"total_income (simulated)     = {result.total_income:.3f}")
    print()

    rows = []
    for node_id, node in parsed.nodes.items():
        breakdown = result.nodes.get(node_id)
        if breakdown is None:
            continue
        player = next((c for c in node.countries if c.tag == parsed.player_tag), None)
        save_money = player.money if player else 0.0
        val_sum = sum(c.val for c in node.countries)
        # `current` is retained (post-forward) value -- compare against the
        # simulator's own retained portion, not its gross total_value.
        retained_sim = breakdown.total_value - breakdown.forwarded_value
        err_total = abs(retained_sim - node.current_value)
        err_income = abs(breakdown.player_income - save_money)
        rows.append(
            (
                max(err_total, err_income),
                node_id,
                node.current_value,
                retained_sim,
                val_sum,
                save_money,
                breakdown.player_income,
                node.retention,
            )
        )

    rows.sort(key=lambda r: -r[0])
    header = (
        f"{'node':<20} {'save.current':>12} {'sim.total':>12} {'sum(val)':>12} "
        f"{'save.money':>12} {'sim.income':>12} {'save.retention':>15}"
    )
    print(header)
    print("-" * len(header))
    for _, node_id, save_current, sim_total, val_sum, save_money, sim_income, retention in rows:
        print(
            f"{node_id:<20} {save_current:>12.3f} {sim_total:>12.3f} {val_sum:>12.3f} "
            f"{save_money:>12.3f} {sim_income:>12.3f} {retention:>15.4f}"
        )


if __name__ == "__main__":
    main()
