"""Loaded saves, kept in memory between requests: the app works on one save at a time and sends only the player's
decisions, so the world (every country in every node, about 1-2 MB of numbers) never travels to the browser.

A session is keyed by the hash of the uploaded file; the newest few are kept. After a server restart the browser
must upload the save again (the API answers 404 with a message saying so).
"""
from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict
from dataclasses import dataclass, field, replace
from pathlib import Path

from app.parsing.tradenodes import load_trade_graph
from app.trade import calc
from app.trade.extract import extract_world
from app.trade.types import World

MAX_SESSIONS = 4


@dataclass
class Session:
    save_id: str
    world: World
    observed: calc.Observed
    _what_if: dict[tuple, calc.WhatIf] = field(default_factory=dict)

    @property
    def player(self) -> str:
        return self.world.inputs.player

    def observed_with(self, trade_efficiency: float | None = None, power_per_light_ship: float | None = None) -> calc.Observed:
        """The save's observed scalars with the player's trade efficiency / power per light ship replaced (sliders)."""
        obs = self.observed
        if trade_efficiency is not None:
            obs = replace(obs, trade_efficiency=obs.trade_efficiency | {self.player: trade_efficiency})
        if power_per_light_ship is not None:
            obs = replace(obs, ship_unit_power=obs.ship_unit_power | {self.player: power_per_light_ship})
        return obs

    def what_if(self, trade_efficiency: float | None = None, power_per_light_ship: float | None = None) -> calc.WhatIf:
        key = (trade_efficiency, power_per_light_ship)
        if key not in self._what_if:
            if len(self._what_if) > 8:
                self._what_if.clear()
            self._what_if[key] = calc.WhatIf(self.world.inputs, self.observed_with(*key), self.player)
        return self._what_if[key]


_sessions: OrderedDict[str, Session] = OrderedDict()
_lock = threading.Lock()


def load(path: Path, filename: str) -> Session:
    save_id = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    with _lock:
        if save_id in _sessions:
            _sessions.move_to_end(save_id)
            return _sessions[save_id]
    world = extract_world(path, filename, graph=load_trade_graph())
    session = Session(save_id, world, calc.identify_observed(world))
    with _lock:
        _sessions[save_id] = session
        while len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)
    return session


def get(save_id: str) -> Session | None:
    with _lock:
        s = _sessions.get(save_id)
        if s is not None:
            _sessions.move_to_end(save_id)
        return s
