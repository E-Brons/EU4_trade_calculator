"""Build backend/data/tradenodes.json from the EU4 game files.

Usage:
    python3 scripts/build_tradenodes.py [path-to-eu4-install]

If no path is given, a few common Steam install locations are tried. The
output is a self-contained JSON file (node graph only - no textures/paths)
so the app runs without a local EU4 install.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.parsing.clausewitz import parse, as_list

DEFAULT_INSTALL_CANDIDATES = [
    "~/Library/Application Support/Steam/steamapps/common/Europa Universalis IV",
    "~/.steam/steam/steamapps/common/Europa Universalis IV",
    "C:/Program Files (x86)/Steam/steamapps/common/Europa Universalis IV",
]


def find_install() -> Path:
    for candidate in DEFAULT_INSTALL_CANDIDATES:
        p = Path(candidate).expanduser()
        if (p / "common" / "tradenodes").exists():
            return p
    raise SystemExit(
        "Could not find an EU4 install. Pass the install directory as an argument."
    )


def build(install_dir: Path) -> dict:
    tradenodes_file = install_dir / "common" / "tradenodes" / "00_tradenodes.txt"
    text = tradenodes_file.read_text(encoding="utf-8-sig")
    tree = parse(text)

    # Node display names come from localisation; fall back to a title-cased
    # key if no localisation entry is found.
    loc_names = load_localisation(install_dir)

    nodes = {}
    for name, body in tree.items():
        outgoing = [
            {"target": og["name"]} for og in as_list(body.get("outgoing"))
        ]
        nodes[name] = {
            "id": name,
            "display_name": loc_names.get(name, name.replace("_", " ").title()),
            "location": body.get("location"),
            "inland": bool(body.get("inland", False)),
            "outgoing": outgoing,
            "member_provinces": as_list(body.get("members")),
        }

    end_nodes = sorted(n for n, v in nodes.items() if not v["outgoing"])
    return {
        "game_version": "1.37",
        "node_count": len(nodes),
        "end_nodes": end_nodes,
        "nodes": nodes,
    }


def load_localisation(install_dir: Path) -> dict[str, str]:
    """Best-effort lookup of trade node display names from the English
    localisation yml files (key format: ``<node_id>:0 "Display Name"``)."""
    names: dict[str, str] = {}
    loc_dir = install_dir / "localisation"
    if not loc_dir.exists():
        return names
    for yml in loc_dir.glob("*_l_english.yml"):
        try:
            text = yml.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, rest = line.partition(":")
            key = key.strip()
            rest = rest.strip()
            if not rest.startswith((" ", '"')) and not rest[:1].isdigit():
                continue
            # rest looks like: 0 "Display Name"  (version number then string)
            quote_start = rest.find('"')
            quote_end = rest.rfind('"')
            if quote_start == -1 or quote_end == quote_start:
                continue
            names[key] = rest[quote_start + 1 : quote_end]
    return names


def main() -> None:
    if len(sys.argv) > 1:
        install_dir = Path(sys.argv[1]).expanduser()
    else:
        install_dir = find_install()

    data = build(install_dir)
    out_path = Path(__file__).resolve().parent.parent / "data" / "tradenodes.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"Wrote {data['node_count']} nodes to {out_path}")
    print(f"End nodes: {data['end_nodes']}")


if __name__ == "__main__":
    main()
