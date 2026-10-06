"""Catalogue of every situation that can change the result of the trade calculation.

Each case has an id, a predicate over the extracted World (so the fixture corpus can be checked for coverage), and the
research tasks that govern it. tests/trade/test_coverage.py requires every case to be exhibited by at least one fixture
save (intervention cases: by a fixture whose manifest `covers` lists the id), or to be explicitly listed as known
uncovered. `expect_absent` cases must never occur in a real save (they guard our assumptions).
docs/trade_spec.md is generated from this file (scripts/gen_spec.py).
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

from app.parsing.tradenodes import TradeGraph
from app.trade.types import EntryInput, World

_COLONIAL = re.compile(r"^C\d\d$")


@dataclass(frozen=True)
class EdgeCase:
    id: str
    title: str
    level: str                      # entry | node | world | intervention
    description: str
    research: tuple[str, ...] = ()
    predicate: Callable | None = None
    expect_absent: bool = False


@dataclass
class Ctx:
    world: World
    graph: TradeGraph
    by_node: dict[str, list[EntryInput]]


def _ctx(world: World, graph: TradeGraph) -> Ctx:
    by_node: dict[str, list[EntryInput]] = defaultdict(list)
    for e in world.inputs.entries.values():
        by_node[e.node].append(e)
    return Ctx(world, graph, by_node)


def _plain(e: EntryInput) -> bool:
    return not e.collecting and not e.steering and not e.has_capital


def _rec(c: Ctx, e: EntryInput):
    return c.world.recorded.entries.get((e.node, e.tag))


def _half_multiple(x: float) -> bool:
    return abs(x * 2 - round(x * 2)) < 0.01


ENTRY_CASES: tuple[EdgeCase, ...] = (
    EdgeCase("EC-P01", "capital node, merchant present", "entry", "Country's capital is in the node and a merchant is present.", ("R06", "R07"), lambda e, c: e.has_capital and e.has_trader),
    EdgeCase("EC-P02", "capital node, no merchant", "entry", "Capital node without a merchant (the game still collects).", ("R06", "R07"), lambda e, c: e.has_capital and not e.has_trader),
    EdgeCase("EC-P03", "merchant collecting away from capital", "entry", "Collecting merchant in a node that is not the capital node.", ("R02", "R06", "R07"), lambda e, c: e.collecting and not e.has_capital),
    EdgeCase("EC-P04", "steering merchant", "entry", "Merchant steering value to a link.", ("R06", "R08"), lambda e, c: e.steering),
    EdgeCase("EC-P05", "passive presence with province power", "entry", "No merchant action, owns provinces in the node.", ("R03",), lambda e, c: _plain(e) and e.province_power > 0),
    EdgeCase("EC-P06", "propagated-only presence", "entry", "No provinces or ships, power only from propagation.", ("R05",), lambda e, c: e.province_power == 0 and e.ship_power == 0 and ((_rec(c, e).prev or 0) > 0 if _rec(c, e) else False)),
    EdgeCase("EC-P07", "merchant with no recorded action", "entry", "Merchant present but neither steering nor marked collecting.", ("R06",), lambda e, c: e.has_trader and not e.steering and not e.collecting and not e.has_capital),
    EdgeCase("EC-S01", "ships at the capital node", "entry", "Light ships assigned to the capital node.", ("R11",), lambda e, c: e.light_ships > 0 and e.has_capital),
    EdgeCase("EC-S02", "ships at a steering node", "entry", "Light ships assigned to a node where the merchant steers.", ("R11",), lambda e, c: e.light_ships > 0 and e.steering),
    EdgeCase("EC-S03", "ships at an away-collecting node", "entry", "Light ships assigned to a node collected away from the capital.", ("R02", "R11"), lambda e, c: e.light_ships > 0 and e.collecting and not e.has_capital),
    EdgeCase("EC-S04", "ships at a passive node", "entry", "Light ships in a node without merchant action.", ("R11",), lambda e, c: e.light_ships > 0 and _plain(e)),
    EdgeCase("EC-S05", "ships in an inland node", "entry", "Impossible in the game; guards our assumption.", ("R11",), lambda e, c: e.light_ships > 0 and c.graph.is_inland(e.node), True),
    EdgeCase("EC-S06", "non-standard power per ship", "entry", "ship_power/ship is not a multiple of 0.5: mixed fleet or ship-power modifier.", ("R11",), lambda e, c: e.light_ships > 0 and not _half_multiple(e.ship_power / e.light_ships)),
    EdgeCase("EC-M01", "node modifier present", "entry", "A modifier block (merchant_recalled, pirate_hunting, ...) on the country entry.", ("R06",), lambda e, c: bool(e.modifiers)),
    EdgeCase("EC-M02", "negative node modifier power", "entry", "A node modifier with negative flat power.", ("R06",), lambda e, c: any(m.power < 0 for m in e.modifiers)),
    EdgeCase("EC-T01", "transfers power out", "entry", "Country gives trade power to another (subject/colony/diplomatic).", ("R04",), lambda e, c: e.t_out > 0),
    EdgeCase("EC-T02", "receives transferred power", "entry", "Country receives trade power from another.", ("R04",), lambda e, c: e.t_in > 0),
    EdgeCase("EC-T03", "colonial nation entry", "entry", "A colonial nation (tag C00..C99) is present.", ("R04",), lambda e, c: bool(_COLONIAL.match(e.tag))),
)

NODE_CASES: tuple[EdgeCase, ...] = (
    EdgeCase("EC-N01", "end node", "node", "Node without outgoing links; has no pull_power key.", ("R03",), lambda n, c: not c.graph.outgoing(n)),
    EdgeCase("EC-N02", "single outgoing link", "node", "All forwarded value goes to one node.", ("R08",), lambda n, c: len(c.graph.outgoing(n)) == 1),
    EdgeCase("EC-N03", "two outgoing links", "node", "Forwarded value is split over two links.", ("R08",), lambda n, c: len(c.graph.outgoing(n)) == 2),
    EdgeCase("EC-N04", "three or more outgoing links", "node", "Forwarded value is split over three or more links.", ("R08",), lambda n, c: len(c.graph.outgoing(n)) >= 3),
    EdgeCase("EC-N05", "retention zero", "node", "Nothing retained: all value is forwarded.", ("R03",), lambda n, c: c.world.recorded.nodes[n].retention == 0 and (c.world.inputs.nodes[n].local_value > 0)),
    EdgeCase("EC-N06", "retention one", "node", "Everything retained.", ("R03",), lambda n, c: (c.world.recorded.nodes[n].retention or 0) >= 0.9995),
    EdgeCase("EC-N07", "zero-value node", "node", "Node with no value at all.", (), lambda n, c: c.world.inputs.nodes[n].local_value == 0 and not c.world.recorded.nodes[n].incoming),
    EdgeCase("EC-N08", "trade company region", "node", "Node flagged trade_company_region.", ("R04",), lambda n, c: c.world.inputs.nodes[n].trade_company_region),
    EdgeCase("EC-N09", "pirate collector power", "node", "collector_power_including_pirates exceeds collector_power.", ("R10",), lambda n, c: (c.world.recorded.nodes[n].collector_power_including_pirates or 0) - (c.world.recorded.nodes[n].collector_power or 0) > 0.001),
    EdgeCase("EC-N10", "multiple collectors", "node", "Two or more countries collect in the node.", ("R07",), lambda n, c: sum(1 for e in c.by_node[n] if e.collecting or e.has_capital) >= 2),
    EdgeCase("EC-N11", "multiple capitals in node", "node", "Two or more countries have their capital in the node.", ("R06",), lambda n, c: sum(1 for e in c.by_node[n] if e.has_capital) >= 2),
    EdgeCase("EC-N12", "nobody steers", "node", "Node with outgoing links and value but no steering merchant.", ("R08",), lambda n, c: bool(c.graph.outgoing(n)) and (c.world.recorded.nodes[n].outgoing or 0) > 0 and not any(e.steering for e in c.by_node[n])),
)

WORLD_CASES: tuple[EdgeCase, ...] = (
    EdgeCase("EC-I01", "country with several collecting nodes", "world", "At least one country collects in two or more nodes (the only way to cross-check trade efficiency).", ("R07",),
             lambda w, c: any(n >= 2 for n in _collect_counts(w).values())),
    EdgeCase("EC-W01", "mods enabled", "world", "The save lists enabled mods.", (), lambda w, c: bool(w.inputs.mods)),
    EdgeCase("EC-W02", "melted Ironman save", "world", "Save came from a binary Ironman file melted by pdx.tools.", ("R12",), lambda w, c: w.inputs.ironman),
    EdgeCase("EC-W03", "unsupported game version", "world", "Save is not from the supported game version; guards our assumption.", ("R12",), lambda w, c: w.inputs.game_version != "1.37.5", True),
    EdgeCase("EC-W04", "player has away-collecting merchant", "world", "The player collects away from the capital.", ("R02", "R07"),
             lambda w, c: any(e.tag == w.inputs.player and e.collecting and not e.has_capital for e in w.inputs.entries.values())),
    EdgeCase("EC-W05", "player has light ships", "world", "The player has light ships assigned somewhere.", ("R11",),
             lambda w, c: any(e.tag == w.inputs.player and e.light_ships > 0 for e in w.inputs.entries.values())),
)

INTERVENTION_CASES: tuple[EdgeCase, ...] = tuple(
    EdgeCase(i, t, "intervention", "Counterfactual: needs an intervention-pair fixture (docs/research/R14).", ("R14",))
    for i, t in (
        ("IV-01", "merchant none -> collect at capital"), ("IV-02", "merchant none -> collect away"),
        ("IV-03", "merchant none -> steer to each link"), ("IV-04", "steer link A -> link B"),
        ("IV-05", "two merchants steering the same link"), ("IV-06", "ships added at capital"),
        ("IV-07", "ships added at steering node"), ("IV-08", "ships added at away-collecting node"),
        ("IV-09", "ships added at passive node"), ("IV-10", "ship type mix"),
        ("IV-11", "merchant recalled"), ("IV-12", "embargo on/off"), ("IV-13", "transfer trade power on/off"),
        ("IV-14", "trade company region node"), ("IV-15", "capital moved"), ("IV-16", "trade-efficiency idea unlocked"),
    )
)

CASES: tuple[EdgeCase, ...] = ENTRY_CASES + NODE_CASES + WORLD_CASES + INTERVENTION_CASES
BY_ID = {c.id: c for c in CASES}


def _collect_counts(world: World) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for e in world.inputs.entries.values():
        if e.collecting or e.has_capital:
            counts[e.tag] += 1
    return counts


def classify_entry(ctx: Ctx, e: EntryInput) -> frozenset[str]:
    return frozenset(c.id for c in ENTRY_CASES if c.predicate(e, ctx))


def classify_node(ctx: Ctx, node: str) -> frozenset[str]:
    return frozenset(c.id for c in NODE_CASES if c.predicate(node, ctx))


def classify_world(ctx: Ctx) -> frozenset[str]:
    return frozenset(c.id for c in WORLD_CASES if c.predicate(ctx.world, ctx))


def make_ctx(world: World, graph: TradeGraph) -> Ctx:
    return _ctx(world, graph)


def present_cases(ctx: Ctx) -> dict[str, int]:
    """Occurrence count per case id in this world (entry/node/world levels)."""
    counts: dict[str, int] = defaultdict(int)
    for e in ctx.world.inputs.entries.values():
        for cid in classify_entry(ctx, e):
            counts[cid] += 1
    for n in ctx.world.recorded.nodes:
        for cid in classify_node(ctx, n):
            counts[cid] += 1
    for cid in classify_world(ctx):
        counts[cid] += 1
    return dict(counts)
