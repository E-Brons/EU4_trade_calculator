"""Adding a save to a research dataset (backend/scripts/add_save.py). Rejects anything that is not a fair test.

Checks, in order: the save is clean (quality.py: the 1st after the game's first computation, none of the player's
merchants or fleets on the way, supported game version); its dataset is the one its version / rule-changing mods / DLC
set select; for a C or B save, the series' A exists and is the same game (player, start date, multiplayer_random_seed;
with reloaded=True only player and start date: EU4 draws a new multiplayer_random_seed and campaign_id on every load,
verified 2026-10-07, so a save made by reloading A never keeps A's seed) at an earlier date; a C (control) must have the same merchant and ship placements as its A, a B must differ from it.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.parsing.tradenodes import load_trade_graph
from app.trade import cases, corpus, quality, savefile
from app.trade.extract import extract_world
from app.trade.types import WorldInputs

ROLE = re.compile(r"^(observation|A|C|C'|B\d+)$")


class Rejected(Exception):
    """The save cannot be used; the message says why."""


@dataclass
class Added:
    id: str
    file: str
    series_dir: Path
    placements_changed: list[str] = field(default_factory=list)


def _date_key(date: str) -> tuple[int, ...]:
    return tuple(int(x) for x in date.split("."))


def placements(inputs: WorldInputs) -> dict[str, tuple]:
    """The player's merchant and ship placements per node (what an experiment changes)."""
    out = {}
    for (node, tag), e in inputs.entries.items():
        if tag != inputs.player:
            continue
        d = inputs.decisions.get(tag, node)
        if d.action.value != "none" or e.has_trader or e.light_ships:
            out[node] = (d.action.value, e.steer_link if e.steering else None, e.has_trader, e.light_ships)
    return out


def _ensure_dataset(root: Path, q: quality.SaveQuality, inputs: WorldInputs) -> Path:
    d = corpus.dataset_dir(q.game_version, q.mods_key, q.dlc_key, root)
    meta = d / "dataset.json"
    if not meta.exists():
        d.mkdir(parents=True, exist_ok=True)
        meta.write_text(json.dumps({
            "game": "eu4", "game_version": q.game_version, "mods_key": q.mods_key,
            "rule_mods": sorted(m for m in inputs.mods if m not in quality.cosmetic_mods()),
            "cosmetic_mods_present": sorted(m for m in inputs.mods if m in quality.cosmetic_mods()),
            "dlc_key": q.dlc_key, "dlcs": sorted(inputs.dlcs), "protocol": "docs/research/experiments.md",
        }, indent=2) + "\n", encoding="utf-8")
    return d


def add_save(path: Path, series: str, role: str, change: str, covers: list[str] | None = None,
             description: str = "", root: Path = corpus.DATASETS_DIR, reloaded: bool = False) -> Added:
    if not ROLE.match(role):
        raise Rejected(f"role must be observation, A, C, C' or B<n>, not {role!r}")
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", series) or series == "reports":
        raise Rejected(f"series name {series!r}: use lowercase letters, digits and '-' (and not 'reports')")
    text = savefile.read_save_text(path)
    world = extract_world(path, path.name, graph=load_trade_graph())
    q = quality.classify(world.inputs)
    if not q.version_supported:
        raise Rejected(f"game version {q.game_version} is not the supported one")
    if q.timing != quality.TICK_DAY:
        raise Rejected(f"saved on {world.inputs.date} ({q.timing}): save on the 1st of a month, after the first computation")
    if q.own_merchants_in_transit or q.own_fleets_in_transit:
        raise Rejected(f"{q.own_merchants_in_transit} of your merchants and {q.own_fleets_in_transit} of your fleets are still on the way: "
                       "wait until they have arrived and save on the next 1st")

    series_dir = _ensure_dataset(root, q, world.inputs) / series
    manifest_path = series_dir / "series.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "series": series, "kind": "experiment" if role != "observation" else "observation", "description": description, "saves": []}
    body = cases.flat_text(text)
    digest = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    if any(e.get("sha256") == digest for e in data["saves"]):
        raise Rejected("this save is already in the series")
    seed = savefile.extract_scalar(text.gamestate, "multiplayer_random_seed") or ""

    changed: list[str] = []
    if role != "observation" and role != "A":
        base = next((e for e in data["saves"] if e["role"] == "A"), None)
        if base is None:
            raise Rejected(f"series {series} has no A save yet: add the baseline first (--role A)")
        same = (base["tag"], base.get("start_date")) == (world.inputs.player, world.inputs.start_date)
        if not same or (not reloaded and base.get("seed") != seed):
            raise Rejected(f"not the same game as {base['id']} (player, start date or multiplayer_random_seed differ; "
                           "a save made by reloading A gets a new seed: pass reloaded=True / --reloaded)")
        if _date_key(world.inputs.date) <= _date_key(base["date"]):
            raise Rejected(f"saved on {world.inputs.date}, not after the A save ({base['date']})")
        before = base.get("placements", {})
        now = {k: list(v) for k, v in placements(world.inputs).items()}
        changed = sorted(n for n in set(before) | set(now) if before.get(n) != now.get(n))
        if role.startswith("C") and changed:
            raise Rejected(f"a control (C) must keep A's merchant and ship placements; changed at: {', '.join(changed)}")
        if role.startswith("B") and not changed:
            raise Rejected("a B save must change a merchant or ship placement of A (or record a non-placement change with role observation)")
    elif role == "A" and any(e["role"] == "A" for e in data["saves"]):
        raise Rejected(f"series {series} already has an A save")

    number = cases.next_case_number(cases.Store(root, series_dir))
    file = cases.case_filename(number, world.inputs.player, world.inputs.date)
    series_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(series_dir / f"{file}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(file, body)
    entry = {
        "id": f"U{number:02d}", "file": file, "tag": world.inputs.player, "date": world.inputs.date, "role": role,
        "base": next((e["id"] for e in data["saves"] if e["role"] == "A"), None) if role not in ("A", "observation") else None,
        "change": change, "covers": covers or [], "sha256": digest,
        "start_date": world.inputs.start_date, "seed": seed, "reloaded_from_a": reloaded,
        "placements": {k: list(v) for k, v in placements(world.inputs).items()}, "placements_changed": changed,
        "quality": q.to_dict() | quality.ai_in_transit(text.gamestate, world.inputs.player, world.inputs.node_order),
    }
    data["saves"].append(entry)
    tmp = manifest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(manifest_path)
    return Added(entry["id"], file, series_dir, changed)
