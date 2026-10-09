"""Is a save a fair test of the calculation? (R12 final: trade is computed once a month, on the 1st.)

A save written on another day pairs today's merchant/ship flags with the numbers of the last 1st; a save written before
the first 1st of a game holds placeholders (no computation yet). Only a save from the 1st, after the first computation,
with none of the player's own merchants or fleets on the way, can be required to match exactly ("clean").
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

from app.parsing.clausewitz import as_list, parse
from app.trade import calc, savefile
from app.trade.types import WorldInputs

TICK_DAY, MID_MONTH, PRE_FIRST_TICK, UNKNOWN = "tick_day", "mid_month", "pre_first_tick", "unknown"
COSMETIC_MODS_PATH = Path(__file__).resolve().parents[3] / "datasets" / "eu4" / "cosmetic_mods.json"


@lru_cache(maxsize=1)
def cosmetic_mods() -> frozenset[str]:
    return frozenset(json.loads(COSMETIC_MODS_PATH.read_text(encoding="utf-8"))["mods"]) if COSMETIC_MODS_PATH.exists() else frozenset()


def _ymd(date: str) -> tuple[int, int, int] | None:
    try:
        y, m, d = (int(x) for x in date.split("."))
        return y, m, d
    except ValueError:
        return None


def timing(date: str, start_date: str) -> str:
    """tick_day / mid_month / pre_first_tick. The first computation is the first 1st strictly after the start date."""
    now, start = _ymd(date), _ymd(start_date)
    if now is None:
        return UNKNOWN
    if start is not None:
        first_tick = (start[0] + (start[1] == 12), start[1] % 12 + 1, 1)
        if now < first_tick:
            return PRE_FIRST_TICK
    return TICK_DAY if now[2] == 1 else MID_MONTH


def _key(prefix: str, names) -> str:
    return prefix + hashlib.sha256("\n".join(sorted(names)).encode()).hexdigest()[:8]


def mods_key(mods: tuple[str, ...]) -> str:
    """Dataset folder for a mod list: 'vanilla' when every mod is a known cosmetic one (datasets/eu4/cosmetic_mods.json),
    else 'mods-' + 8 hex of the sorted names of the other mods."""
    rule_mods = [m for m in mods if m not in cosmetic_mods()]
    return "vanilla" if not rule_mods else _key("mods-", rule_mods)


def dlc_key(dlcs: tuple[str, ...]) -> str:
    """Dataset folder for a DLC set (DLCs change trade mechanics): 'dlc-' + 8 hex of the sorted DLC names."""
    return _key("dlc-", dlcs)


@dataclass(frozen=True)
class SaveQuality:
    timing: str
    own_merchants_in_transit: int
    own_fleets_in_transit: int
    game_version: str
    version_supported: bool
    mods_key: str
    dlc_key: str

    @property
    def clean(self) -> bool:
        return (self.timing == TICK_DAY and self.version_supported
                and not self.own_merchants_in_transit and not self.own_fleets_in_transit)

    def to_dict(self) -> dict:
        return asdict(self) | {"clean": self.clean}


def classify(inputs: WorldInputs) -> SaveQuality:
    return SaveQuality(
        timing=timing(inputs.date, inputs.start_date),
        own_merchants_in_transit=inputs.own_merchants_in_transit,
        own_fleets_in_transit=inputs.own_fleets_in_transit,
        game_version=inputs.game_version,
        version_supported=inputs.game_version == calc.SUPPORTED_GAME_VERSION,
        mods_key=mods_key(inputs.mods),
        dlc_key=dlc_key(inputs.dlcs),
    )


def ai_in_transit(gamestate: str, player: str, node_order: tuple[str, ...]) -> dict:
    """Other countries' merchants (envoy action 1) and protect fleets without `on_my_way`, with the fleets' target
    nodes. Allowed in a clean save (absent from both trade entries and computed values), recorded for the dataset.
    Parses the whole countries block: for the audit and intake, not for every app upload."""
    block = savefile.extract_top_level_block(gamestate, "countries")
    countries = parse(block[1:-1]) if block else {}
    merchants = fleets = 0
    targets: dict[str, int] = {}
    for tag, c in countries.items():
        if tag == player or not isinstance(c, dict):
            continue
        m = c.get("merchants")
        merchants += sum(1 for v in (as_list(m.get("envoy")) if isinstance(m, dict) else []) if isinstance(v, dict) and v.get("action") == 1)
        for fleet in as_list(c.get("navy")):
            mission = fleet.get("mission") if isinstance(fleet, dict) else None
            pm = mission.get("protect_mission") if isinstance(mission, dict) else None
            if isinstance(pm, dict) and "on_my_way" not in pm:
                fleets += 1
                i = int(pm.get("node", 0))
                node = node_order[i - 1] if 0 < i <= len(node_order) else f"#{i}"
                targets[node] = targets.get(node, 0) + 1
    return {"ai_merchants_in_transit": merchants, "ai_fleets_in_transit": fleets,
            "ai_fleet_targets": ", ".join(f"{n} {k}" for n, k in sorted(targets.items(), key=lambda kv: -kv[1]))}
