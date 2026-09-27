"""Debug helper: melt a save (if needed) and dump the raw parsed structure
of one trade node + the player's tag, to calibrate save.py's field-name
aliases against a real save.

Usage:
    python3 scripts/inspect_save.py path/to/Save.eu4 [node_id]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing.save import load_save


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    save_path = Path(sys.argv[1])
    node_id = sys.argv[2] if len(sys.argv) > 2 else None

    parsed = load_save(save_path)
    print(f"player_tag = {parsed.player_tag}")
    if parsed.warnings:
        print("warnings:")
        for w in parsed.warnings:
            print(f"  - {w}")
    print(f"nodes found: {len(parsed.nodes)}")

    if node_id is None:
        # Prefer a node the player actually has provinces/power in.
        for nid, node in parsed.nodes.items():
            if any(c.tag == parsed.player_tag for c in node.countries):
                node_id = nid
                break
        else:
            node_id = next(iter(parsed.nodes), None)

    if node_id is None or node_id not in parsed.nodes:
        print("No node to show.")
        return

    node = parsed.nodes[node_id]
    print(f"\n--- node: {node_id} ---")
    print(f"local_value={node.local_value} total_value={node.total_value} steer_power_weights={node.steer_power_weights}")
    for c in node.countries:
        print(f"\n  country tag={c.tag}")
        print(f"    parsed: province_power={c.province_power} ship_power={c.ship_power} "
              f"light_ships={c.light_ships} has_capital={c.has_capital} has_trader={c.has_trader} "
              f"is_steering={c.is_steering} val={c.val} money={c.money}")
        print(f"    raw keys: {sorted(c.raw.keys())}")
        print(f"    raw: {json.dumps(c.raw, indent=2, default=str)[:2000]}")


if __name__ == "__main__":
    main()
