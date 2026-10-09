"""calc.WhatIf (the optimizer's fast path) gives exactly what calc.calculate gives for the same decisions, and the
optimizer built on it respects its budgets and never ends below the save's own placement."""
from __future__ import annotations

import dataclasses
import random

import pytest

from app.parsing.tradenodes import load_trade_graph
from app.trade import calc, corpus
from app.trade.optimize import OptimizeConfig, merchants_used, optimize, ships_used
from app.trade.types import Action, Decisions, NodeDecision

SAVES = ("U04", "U30", "U84")   # TUR 1691 (transfers, 134 ships), VEN 1444, FRA 1789


@pytest.fixture(scope="module")
def worlds():
    entries = [e for e in corpus.manifest() if e["id"] in SAVES]
    found = [w for _e, w in corpus.iter_worlds(entries)]
    if not found:
        pytest.skip("dataset saves not available (git lfs pull)")
    return found


def _observed(world):
    obs = calc.identify_observed(world)
    tag = world.inputs.player
    if tag not in calc.ship_unit_power(world.inputs, obs):
        obs = dataclasses.replace(obs, ship_unit_power={tag: 3.0})
    return obs


def _random_placements(world, n: int, seed: int = 1):
    graph = load_trade_graph()
    tag = world.inputs.player
    base = {node: d for (t, node), d in world.inputs.decisions.by_entry.items() if t == tag}
    nodes = sorted({node for (node, t) in world.inputs.entries if t == tag})
    rng = random.Random(seed)
    for _ in range(n):
        p = dict(base)
        for _ in range(rng.randint(0, 4)):
            node = rng.choice(nodes)
            cur = p.get(node, NodeDecision())
            kind = rng.choice(["none", "collect", "steer", "ships"])
            if kind == "none":
                p[node] = NodeDecision(Action.NONE, None, cur.light_ships)
            elif kind == "collect":
                p[node] = NodeDecision(Action.COLLECT, None, cur.light_ships)
            elif kind == "steer" and graph.outgoing(node):
                p[node] = NodeDecision(Action.STEER, rng.choice(graph.outgoing(node)), cur.light_ships)
            elif not graph.is_inland(node):
                p[node] = NodeDecision(cur.action, cur.steer_target, rng.randint(0, 15))
        yield p


def test_what_if_equals_full_calculation(worlds):
    for world in worlds:
        obs, tag = _observed(world), world.inputs.player
        what_if = calc.WhatIf(world.inputs, obs, tag)
        others = {k: d for k, d in world.inputs.decisions.by_entry.items() if k[0] != tag}
        for p in _random_placements(world, 25):
            fast = what_if.evaluate(p)
            full = calc.calculate(world.inputs, Decisions(others | {(tag, n): d for n, d in p.items()}), obs)
            assert fast.income(tag) == pytest.approx(full.income(tag), abs=1e-9)
            for node, nr in full.nodes.items():
                assert fast.nodes[node].current == pytest.approx(nr.current, abs=1e-9), (world.save_id, node)
                assert fast.nodes[node].link_values == pytest.approx(nr.link_values, abs=1e-9), (world.save_id, node)


def test_optimizer_respects_budgets_and_beats_the_save(worlds):
    graph = load_trade_graph()
    for world in worlds:
        obs, tag = _observed(world), world.inputs.player
        what_if = calc.WhatIf(world.inputs, obs, tag)
        current = {n: d for (t, n), d in world.inputs.decisions.by_entry.items() if t == tag}
        home = next(n for (n, t), e in world.inputs.entries.items() if t == tag and e.has_capital)
        candidates = sorted({n for (n, t), e in world.inputs.entries.items() if t == tag and (e.province_power > 0 or e.has_capital)} | set(current))
        merchants, ships = merchants_used(current), ships_used(current)
        result = optimize(what_if, graph, OptimizeConfig(home, candidates, merchants, ships, max_restarts=1, starts=[current]))
        assert merchants_used(result.placement) <= merchants
        assert ships_used(result.placement) <= ships
        assert result.income >= what_if.income(current) - 1e-9
        assert result.income == pytest.approx(what_if.income(result.placement))
