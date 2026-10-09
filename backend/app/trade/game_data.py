"""Game constants and tables vendored from the installed game by scripts/build_game_data.py.

calc.py is the only module allowed to import this file (enforced by tests/trade/test_architecture.py), so a game
constant can never be used by a second, divergent implementation.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.parsing.tradenodes import TradeGraph, load_trade_graph

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "game"

SUPPORTED_GAME_VERSION = "1.37.5"


@lru_cache(maxsize=1)
def _defines() -> dict[str, float]:
    """defines.lua constants (generated) plus constants fitted from the saves (empirical.json, with evidence)."""
    out: dict[str, float] = {}
    for filename in ("defines_trade.json", "empirical.json"):
        raw = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
        out.update({name: body["value"] for name, body in raw["defines"].items()})
    return out


@lru_cache(maxsize=1)
def _ships() -> dict[str, float]:
    raw = json.loads((DATA_DIR / "light_ships.json").read_text(encoding="utf-8"))
    return {name: body["trade_power"] for name, body in raw["ships"].items()}


def const(name: str) -> float:
    """A defines.lua constant; KeyError if the name was never vendored (never a silent default)."""
    return _defines()[name]


def light_ship_trade_power(ship_type: str) -> float:
    return _ships()[ship_type]


def light_ship_types() -> frozenset[str]:
    return frozenset(_ships())


@lru_cache(maxsize=1)
def country_modifier_sources() -> dict:
    """Per source (idea group/idea, policy, reform, age ability, event or static modifier) the values of the
    country-scope modifiers listed under `modifiers` (country_modifiers.json; only non-zero sources)."""
    return json.loads((DATA_DIR / "country_modifiers.json").read_text(encoding="utf-8"))


def graph() -> TradeGraph:
    return load_trade_graph()
