"""THE trade calculation. The only file with trade arithmetic and the only importer of game constants.

Everything else only feeds it (extract.py), checks it (verify.py, tests) or calls it (optimizer, API).
Rules marked HYPOTHESIS are the best current reading of the data; verification reports them RED until a research
result (docs/research/Rxx) turns them into confirmed rules. Where a variable is truly unknown the code raises
UnknownVariable; it never substitutes a default.

Two entry points share the same rule functions:
  calculate(inputs, decisions, observed)  - the whole world from raw variables (what the app and optimizer use)
  predict_stage(stage, world)             - one stage at a time from the save's recorded upstream values, so a
                                            failure is localised to the stage that is wrong (what verify uses)
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict
from functools import lru_cache
from dataclasses import dataclass, field
from typing import Iterable

from app.trade import game_data
from app.trade.types import (
    Action,
    Decisions,
    EntryInput,
    EntryResult,
    NodeDecision,
    NodeResult,
    TradeResult,
    UnknownVariable,
    World,
    WorldInputs,
)

CALC_VERSION = "0.2.0"

STAGE_INFO: dict[str, tuple[str, tuple[str, ...]]] = {
    "propagation": ("prev = sum over downstream nodes with province_power / TRADE_PROPAGATE_DIVIDER >= TRADE_PROPAGATE_THRESHOLD of fx(province_power / TRADE_PROPAGATE_DIVIDER)", ("R05",)),
    "raw_power": ("max_pow = province + ship + prev + capital + node modifiers + the country's merchant power on every merchant entry", ("R06", "R11")),
    "multiplier": ("max_demand: multiplier from max_pow to val (observed input until derived)", ("R01", "R02")),
    "val": ("val = fx(max_pow * max_demand) (3-decimal fixed point, truncated)", ("R01",)),
    "transfers": ("t_out = fx(0.5 * (val - 0.1)) for a subject giving power away; t_in = sum of givers' amounts; potential = fx((t_out - t_in) / total)", ("R04",)),
    "retain_power": ("retain_power = sum over collectors of (val - t_out + t_in)", ("R04",)),
    "pull_power": ("pull_power = effective power of the countries that steer here, or do not collect here and collect or steer downstream (R03 rule B)", ("R03", "R04")),
    "retention": ("retention = retain / (retain + pull)", ("R03",)),
    "current_value": ("current = gross * retention; outgoing = gross - current", ("R12",)),
    "steer_weights": ("weight of link i = sum over steerers on link i of effective power x steering strength / sum over all links", ("R08",)),
    "link_flow": ("value delivered on link i = outgoing * weight_i * (1 + sum of `add` of the entries on link i)", ("R08",)),
    "income_share": ("power_fraction = fx(effective / retain); share = fx(current * power_fraction)", ("R07",)),
    "income_efficiency": ("money = fx(share * (1 + trade_efficiency + merchant bonus))", ("R07",)),
}
STAGES: tuple[str, ...] = tuple(STAGE_INFO)


class NotImplementedStage(Exception):
    """The stage has no rule yet (waiting for research)."""


@dataclass(frozen=True)
class Observed:
    """Country scalars the save does not store and we do not derive yet (kind=observed in the registry)."""

    trade_efficiency: dict[str, float] = field(default_factory=dict)
    merchant_power: dict[str, float] = field(default_factory=dict)
    steering_strength: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Pair:
    """One predicted value next to the value the save recorded."""

    key: str
    predicted: float
    recorded: float
    node: str
    tag: str = ""


# ----------------------------------------------------------------------------------------------------------------
# Rules (one small pure function per rule)
# ----------------------------------------------------------------------------------------------------------------

def rule_propagated_power(province_power_downstream: Iterable[float]) -> float:
    """R05 C-Q2.1/C-Q5.1, R09 C-16 (confirmed): each directly downstream node whose province power reaches
    TRADE_PROPAGATE_THRESHOLD after the divider contributes fx(province_power / TRADE_PROPAGATE_DIVIDER), truncated per
    link; ships do not propagate. OPEN (R05): which links count (start saves: only links with steer weight > 0; played
    saves: not) and MOR's ship term; neither is applied."""
    divider, threshold = game_data.const("TRADE_PROPAGATE_DIVIDER"), game_data.const("TRADE_PROPAGATE_THRESHOLD")
    return sum(rule_fx(p / divider) for p in province_power_downstream if p / divider >= threshold)


def rule_flat_extras(entry: EntryInput, merchant_power: float) -> float:
    """R06 response_1 C-Q1.1/C-Q3.1: capital +TRADE_CAPITAL_POWER, every node modifier's flat power, and the country's
    merchant power on every entry with a merchant whatever its action (0 for entries without one). The merchant power is
    one value per country (0 in all start saves, 2/7/17/22 in played saves); its composition is open, so it is observed."""
    extras = sum(m.power for m in entry.modifiers) + merchant_power
    if entry.has_capital:
        extras += game_data.const("TRADE_CAPITAL_POWER")
    return extras


def rule_merchant_power_residual(e: EntryInput, max_pow: float, prev: float) -> float:
    """What max_pow holds beyond province, ships, prev, capital and modifiers (the merchant power on a merchant entry)."""
    return max_pow - e.province_power - e.ship_power - prev - rule_flat_extras(e, 0.0)


def rule_fx(x: float) -> float:
    """The game stores and computes in 3-decimal fixed point and truncates (found in the data, not in any source):
    val = fx(max_pow * max_demand) in 83,201 of 83,201 entries; power_fraction = fx(effective / retain_power) in
    42,323 of 42,330; share_total = fx(current * power_fraction) in 42,330 of 42,330."""
    scale = game_data.const("FIXED_POINT_SCALE")
    return math.trunc(x * scale + (1e-9 if x >= 0 else -1e-9)) / scale


def rule_max_pow(province_power: float, ship_power: float, prev: float, extras: float) -> float:
    return province_power + ship_power + prev + extras


def rule_val(max_pow: float, multiplier: float) -> float:
    return rule_fx(max_pow * multiplier)


def rule_transfer_out(val: float) -> float:
    """R04 + project check (1,855 of 1,855 givers): a subject gives fx(TRANSFER_FRACTION * (val - TRANSFER_MIN_POWER_KEPT))."""
    return rule_fx(game_data.const("TRANSFER_FRACTION") * (val - game_data.const("TRANSFER_MIN_POWER_KEPT")))


def rule_potential(t_out: float, t_in: float, node_total: float) -> float:
    """R04 + project check (2,991 of 2,991): potential = fx((t_out - t_in) / total), positive for givers, negative for receivers."""
    return rule_fx((t_out - t_in) / node_total) if node_total > 0 else 0.0


def rule_effective_power(val: float, t_out: float, t_in: float) -> float:
    return val - t_out + t_in


def rule_is_collecting(entry: EntryInput, decision: NodeDecision) -> bool:
    return entry.has_capital or decision.action == Action.COLLECT


@lru_cache(maxsize=1)
def _downstream() -> dict[str, frozenset[str]]:
    graph = game_data.graph()
    closure: dict[str, frozenset[str]] = {}

    def visit(node: str) -> frozenset[str]:
        if node not in closure:
            reach: set[str] = set()
            for target in graph.outgoing(node):
                reach.add(target)
                reach |= visit(target)
            closure[node] = frozenset(reach)
        return closure[node]

    for node in graph.nodes:
        visit(node)
    return closure


def rule_is_steering(decision: NodeDecision) -> bool:
    return decision.action == Action.STEER


def rule_is_pulling(node: str, steering: bool, collecting_here: bool, active_nodes: frozenset[str] | set[str]) -> bool:
    """R03 final, rule B (5,895 of 5,896 nodes; the one left is a stale aggregate, C-09): a country pulls in a node when
    it steers there, or does not collect there but collects or steers in some node downstream (any number of hops).
    `active_nodes` = the country's collecting and steering nodes. Others are in neither retain nor pull."""
    return steering or (not collecting_here and bool(active_nodes & _downstream()[node]))


def rule_retain_pull(collectors: Iterable[float], pullers: Iterable[float]) -> tuple[float, float]:
    """retain = sum of effective power of collectors; pull = sum of effective power of pulling countries (R03)."""
    return sum(collectors), sum(pullers)


def rule_away_adjustment(recorded_away: bool, decided_away: bool) -> float:
    """R02 final C-01/C-02 (188 of 189 away collectors; steering, idle merchants and home collectors are not penalised):
    max_demand includes a multiplicative 0.5 (1 + TRADE_NON_CAPITAL_OFFICE) while a merchant collects away from the
    home node. Changing that status changes max_demand by 0.5 either way; unchanged decisions leave the recorded value."""
    factor = 1.0 + game_data.const("TRADE_NON_CAPITAL_OFFICE")
    return (factor if decided_away else 1.0) / (factor if recorded_away else 1.0)


def rule_retention(retain: float, pull: float) -> float:
    """retain / (retain + pull) (confirmed). With no power at all in the node everything is retained (recorded 1.0)."""
    total = retain + pull
    return retain / total if total > 0 else 1.0


def rule_current_outgoing(gross: float, retention: float) -> tuple[float, float]:
    current = gross * retention
    return current, gross - current


def rule_steer_weights(link_count: int, steerers: Iterable[tuple[int, float, float | None]]) -> tuple[float, ...]:
    """R08 response_1 W-3 (119 of 120 testable tick-day nodes): weight of link i = sum over the steering merchants on
    link i of effective power x the country's steering strength, divided by the same sum over all links. Passive pullers
    and collectors do not count. A single link carries everything. OPEN: a steerer whose strength is unknown (nan
    result), and nodes with no steerer (R08 Q5)."""
    if link_count == 1:
        return (1.0,)
    per_link = [0.0] * link_count
    for link, power, strength in steerers:
        if power == 0:
            continue
        if strength is None:
            return tuple(math.nan for _ in per_link)
        if link < link_count:
            per_link[link] += power * strength
    total = sum(per_link)
    return tuple(p / total for p in per_link) if total > 0 else tuple(math.nan for _ in per_link)


def rule_steering_strengths(groups: Iterable[list[tuple[str, float, float]]], rounds: int = 2) -> tuple[dict[str, float], dict[str, bool]]:
    """R08 W-2: add = trunc3(strength / rank), rank = order by effective power x strength among the add-carrying steering
    entries of one link. Each entry bounds the strength to [add x rank, (add + 0.001) x rank); a country's strength is
    the value most of its entries agree on. Start: equal strengths (rank by power). Returns strength and whether every
    entry of the country agrees. `groups` = per (node, link): [(tag, effective power, add)]."""
    groups = list(groups)
    strength: dict[str, float] = defaultdict(lambda: 1.0)
    consistent: dict[str, bool] = {}
    for _ in range(rounds):
        bounds: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for items in groups:
            ranked = sorted(items, key=lambda x: -x[1] * strength[x[0]])
            for rank, (tag, _eff, add) in enumerate(ranked, 1):
                bounds[tag].append((add * rank, (add + 1.0 / game_data.const("FIXED_POINT_SCALE")) * rank))
        new: dict[str, float] = {}
        for tag, ivs in bounds.items():
            events = sorted([(lo, 1) for lo, _hi in ivs] + [(hi, -1) for _lo, hi in ivs])
            best, best_at, cur = 0, 0.0, 0
            for i, (x, d) in enumerate(events):
                cur += d
                if d == 1 and cur > best:
                    best, best_at = cur, (x + events[i + 1][0]) / 2
            new[tag] = best_at
            consistent[tag] = best == len(ivs)
        strength = defaultdict(lambda: 1.0, new)
    return dict(strength), consistent


def rule_link_adds(link_count: int, adds: Iterable[tuple[int, float]]) -> tuple[float, ...]:
    """Sum of the `add` of every entry with that key, per steered link (R08 C-05: the key, not `type`, marks it)."""
    per_link = [0.0] * link_count
    for link, add in adds:
        if link < link_count:
            per_link[link] += add
    return tuple(per_link)


def rule_link_values(outgoing: float, weights: tuple[float, ...], link_adds: tuple[float, ...]) -> tuple[float, ...]:
    """R08 C-06 (12,590 of 12,590 links): value on link i = outgoing * weight_i * (1 + sum of `add` on link i); the
    bonus is value created on the link. OPEN (R08): the weights themselves and the size of `add`."""
    return tuple(outgoing * w * (1.0 + a) for w, a in zip(weights, link_adds))


def rule_power_fraction(effective: float, retain: float) -> float:
    """A collector's share of the retained power, in fixed point (truncated)."""
    return rule_fx(effective / retain) if retain > 0 else 0.0


def rule_income_share(current: float, power_fraction: float) -> float:
    """A collector's share of the retained ducats = fx(current * power_fraction) (exact in the data)."""
    return rule_fx(current * power_fraction)


def rule_merchant_bonus(has_trader: bool) -> float:
    """HYPOTHESIS (R07): +TRADE_MERCHANT_PRESENT when a merchant is present."""
    return game_data.const("TRADE_MERCHANT_PRESENT") if has_trader else 0.0


def rule_money(share: float, trade_efficiency: float, merchant_bonus: float) -> float:
    return rule_fx(share * (1.0 + trade_efficiency + merchant_bonus))


def rule_trade_efficiency(money: float, share: float, merchant_bonus: float) -> float:
    return money / share - 1.0 - merchant_bonus


# ----------------------------------------------------------------------------------------------------------------
# Whole-world calculation (inputs only: this function cannot see recorded results)
# ----------------------------------------------------------------------------------------------------------------

def _ship_unit_power(inputs: WorldInputs) -> dict[str, float]:
    ships: dict[str, int] = defaultdict(int)
    power: dict[str, float] = defaultdict(float)
    for e in inputs.entries.values():
        ships[e.tag] += e.light_ships
        power[e.tag] += e.ship_power
    return {t: power[t] / n for t, n in ships.items() if n > 0}


def calculate(inputs: WorldInputs, decisions: Decisions | None = None, observed: Observed | None = None) -> TradeResult:
    graph = game_data.graph()
    decisions = decisions if decisions is not None else inputs.decisions
    observed = observed or Observed()
    unit_power = _ship_unit_power(inputs)

    entries: dict[tuple[str, str], EntryInput] = dict(inputs.entries)
    for (tag, node), d in decisions.by_entry.items():
        if (node, tag) not in entries and (d.action != Action.NONE or d.light_ships):
            entries[(node, tag)] = EntryInput(tag=tag, node=node)

    province_power = {key: e.province_power for key, e in entries.items()}

    entry_results: dict[tuple[str, str], EntryResult] = {}
    first_pass: list[tuple[str, EntryInput, float, bool, bool]] = []
    active_nodes: dict[str, set[str]] = defaultdict(set)   # collecting or steering (R03 rule B)
    for (node, tag), e in entries.items():
        d = decisions.get(tag, node)
        prev = rule_propagated_power(province_power.get((down, tag), 0.0) for down in graph.outgoing(node)) if node in graph else 0.0
        if d.light_ships:
            if d.light_ships == e.light_ships and e.ship_power > 0:
                ship_power = e.ship_power
            elif tag in unit_power:
                ship_power = d.light_ships * unit_power[tag]
            else:
                raise UnknownVariable("ship unit power", f"{tag}@{node}", "R11")
        else:
            ship_power = 0.0
        merchant_present = d.action != Action.NONE or (e.has_trader and inputs.decisions.get(tag, node).action == Action.NONE)
        if merchant_present and tag not in observed.merchant_power:
            raise UnknownVariable("merchant power", tag, "R06")
        max_pow = rule_max_pow(e.province_power, ship_power, prev, rule_flat_extras(e, observed.merchant_power.get(tag, 0.0) if merchant_present else 0.0))
        multiplier = inputs.multipliers.get((node, tag))
        if multiplier is None and max_pow != 0:
            raise UnknownVariable("max_demand", f"{tag}@{node}", "R01")
        collecting = rule_is_collecting(e, d)
        recorded_away = e.collecting and not e.has_capital
        multiplier = (multiplier or 0.0) * rule_away_adjustment(recorded_away, collecting and not e.has_capital)
        val = rule_val(max_pow, multiplier)
        entry_results[(node, tag)] = EntryResult(prev=prev, max_pow=max_pow, val=val, collecting=collecting)
        first_pass.append((node, e, val, collecting, rule_is_steering(d)))
        if collecting or rule_is_steering(d):
            active_nodes[tag].add(node)

    # Transfers (R04): a giver's t_out follows its own val; the amounts it sends to each receiver scale with it.
    t_out_now: dict[tuple[str, str], float] = {}
    t_in_delta: dict[tuple[str, str], float] = defaultdict(float)
    for node, e, val, _c, _s in first_pass:
        if e.t_out > 0:
            new_out = rule_transfer_out(val)
            t_out_now[(node, e.tag)] = new_out
            for receiver, amount in e.transfers_to:
                t_in_delta[(node, receiver)] += amount * (new_out / e.t_out) - amount

    pending: list[tuple[str, EntryInput, float, bool, bool]] = []
    for node, e, val, collecting, steering in first_pass:
        eff = rule_effective_power(val, t_out_now.get((node, e.tag), e.t_out), e.t_in + t_in_delta.get((node, e.tag), 0.0))
        entry_results[(node, e.tag)].effective = eff
        pending.append((node, e, eff, collecting, steering))

    # Steering bonus (R08): the save's `add` of each entry on its link; a newly steering merchant has no known `add`.
    node_adds: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for (node, tag), e in entries.items():
        d = decisions.get(tag, node)
        if rule_is_steering(d) and not e.steering:
            raise UnknownVariable("steering add", f"{tag}@{node}", "R08")
        if e.add is not None and (rule_is_steering(d) or not e.steering):
            node_adds[node].append((e.steer_link, e.add))

    node_effective: dict[str, list[tuple[EntryInput, float, bool, bool]]] = defaultdict(list)
    for node, e, eff, collecting, steering in pending:
        node_effective[node].append((e, eff, collecting, rule_is_pulling(node, steering, collecting, active_nodes[e.tag])))

    node_results: dict[str, NodeResult] = {}
    incoming: dict[str, float] = defaultdict(float)
    for node in graph.topo_order():
        info = inputs.nodes.get(node)
        gross = (info.local_value if info else 0.0) + incoming[node]
        rows = node_effective.get(node, [])
        retain, pull = rule_retain_pull((eff for _e, eff, c, _p in rows if c), (eff for _e, eff, _c, p in rows if p))
        retention = rule_retention(retain, pull)
        targets = graph.outgoing(node)
        current, outgoing = rule_current_outgoing(gross, retention)
        steerers = [(e.steer_link, eff, observed.steering_strength.get(e.tag)) for e, eff, _c, _p in rows if rule_is_steering(decisions.get(e.tag, node))]
        missing = [e.tag for e, eff, _c, _p in rows if rule_is_steering(decisions.get(e.tag, node)) and eff != 0 and e.tag not in observed.steering_strength]
        if len(targets) > 1 and missing:
            raise UnknownVariable("steering strength", f"{missing[0]}@{node}", "R08")
        weights = rule_steer_weights(len(targets), steerers)
        link_values = rule_link_values(outgoing, weights, rule_link_adds(len(targets), node_adds.get(node, [])))
        for target, v in zip(targets, link_values):
            incoming[target] += v
        node_results[node] = NodeResult(
            gross=gross, retain_power=retain, pull_power=pull, retention=retention, current=current, outgoing=outgoing,
            steer_weights=weights, link_values=dict(zip(targets, link_values)),
        )
        for e, eff, c, _p in rows:
            if c:
                r = entry_results[(node, e.tag)]
                r.share_total = rule_income_share(current, rule_power_fraction(eff, retain))
                if e.tag not in observed.trade_efficiency:
                    raise UnknownVariable("trade_efficiency", e.tag, "R07")
                r.money = rule_money(r.share_total, observed.trade_efficiency[e.tag], rule_merchant_bonus(e.has_trader))
    return TradeResult(entries=entry_results, nodes=node_results)


def identify_observed(world: World) -> Observed:
    """Observed (Level 1) country scalars the save does not store:
    trade efficiency, identified at the capital node from the recorded money and share (the income_efficiency stage
    checks it on the country's other collecting nodes);
    merchant power (R06), the most common residual of max_pow over the country's merchant entries (the raw_power stage
    checks that one value fits all of them)."""
    efficiency: dict[str, float] = {}
    residuals: dict[str, Counter[float]] = defaultdict(Counter)
    for (node, tag), e in world.inputs.entries.items():
        rec = world.recorded.entries.get((node, tag))
        if not rec:
            continue
        if e.has_capital and rec.money and rec.share_total and tag not in efficiency:
            efficiency[tag] = rule_trade_efficiency(rec.money, rec.share_total, rule_merchant_bonus(e.has_trader))
        if e.has_trader and rec.max_pow is not None:
            residuals[tag][round(rule_merchant_power_residual(e, rec.max_pow, rec.prev or 0.0), 3)] += 1
    merchant = {tag: c.most_common(1)[0][0] for tag, c in residuals.items()}
    groups: dict[tuple[str, int], list[tuple[str, float, float]]] = defaultdict(list)
    for (node, tag), e in world.inputs.entries.items():
        rec = world.recorded.entries.get((node, tag))
        if e.steering and e.add is not None and rec:
            groups[(node, e.steer_link)].append((tag, rule_effective_power(rec.val or 0.0, e.t_out, e.t_in), e.add))
    strength, _consistent = rule_steering_strengths(groups.values())
    return Observed(trade_efficiency=efficiency, merchant_power=merchant, steering_strength=strength)


# ----------------------------------------------------------------------------------------------------------------
# One stage at a time, from recorded upstream values (isolated; same rule functions as above)
# ----------------------------------------------------------------------------------------------------------------

def _gross_recorded(world: World, node: str) -> float:
    rec = world.recorded.nodes[node]
    return world.inputs.nodes[node].local_value + sum(v for _src, v, _add in rec.incoming)


def predict_stage(stage: str, world: World) -> list[Pair]:
    graph = game_data.graph()
    inp, rec = world.inputs, world.recorded
    out: list[Pair] = []

    if stage == "propagation":
        province_power = {key: e.province_power for key, e in inp.entries.items()}
        for (node, tag), r in rec.entries.items():
            pred = rule_propagated_power(province_power.get((down, tag), 0.0) for down in graph.outgoing(node)) if node in graph else 0.0
            out.append(Pair("prev", pred, r.prev or 0.0, node, tag))

    elif stage == "raw_power":
        observed = identify_observed(world)
        for (node, tag), r in rec.entries.items():
            if r.max_pow is None:
                continue
            e = inp.entries[(node, tag)]
            merchant = observed.merchant_power.get(tag, 0.0) if e.has_trader else 0.0
            pred = rule_max_pow(e.province_power, e.ship_power, r.prev or 0.0, rule_flat_extras(e, merchant))
            out.append(Pair("max_pow", pred, r.max_pow, node, tag))

    elif stage == "multiplier":
        raise NotImplementedStage("max_demand is not derived yet (R01/R02); it is an observed input")

    elif stage == "val":
        for (node, tag), r in rec.entries.items():
            if r.val is None or r.max_pow is None:
                continue
            out.append(Pair("val", rule_val(r.max_pow, inp.multipliers.get((node, tag), 0.0)), r.val, node, tag))

    elif stage == "transfers":
        received: dict[tuple[str, str], float] = defaultdict(float)
        for (node, tag), e in inp.entries.items():
            r = rec.entries[(node, tag)]
            if e.t_out > 0:
                out.append(Pair("t_out", rule_transfer_out(r.val or 0.0), e.t_out, node, tag))
                for receiver, amount in e.transfers_to:
                    received[(node, receiver)] += amount
            nr = rec.nodes[node]
            if r.potential is not None and nr.total:
                out.append(Pair("potential", rule_potential(e.t_out, e.t_in, nr.total), r.potential, node, tag))
        for (node, tag), e in inp.entries.items():
            if e.t_in > 0:
                out.append(Pair("t_in", received.get((node, tag), 0.0), e.t_in, node, tag))

    elif stage in ("retain_power", "pull_power"):
        active_nodes: dict[str, set[str]] = defaultdict(set)
        for (node, tag), e in inp.entries.items():
            d = inp.decisions.get(tag, node)
            if rule_is_collecting(e, d) or rule_is_steering(d):
                active_nodes[tag].add(node)
        per_node: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
        for (node, tag), e in inp.entries.items():
            r = rec.entries[(node, tag)]
            d = inp.decisions.get(tag, node)
            collecting = rule_is_collecting(e, d)
            eff = rule_effective_power(r.val or 0.0, e.t_out, e.t_in)
            if collecting:
                per_node[node][0].append(eff)
            if rule_is_pulling(node, rule_is_steering(d), collecting, active_nodes[tag]):
                per_node[node][1].append(eff)
        for node, nr in rec.nodes.items():
            if stage == "pull_power" and nr.pull_power is None:
                continue
            collectors, pullers = per_node.get(node, ([], []))
            retain, pull = rule_retain_pull(collectors, pullers)
            out.append(Pair(stage, retain if stage == "retain_power" else pull, (nr.retain_power if stage == "retain_power" else nr.pull_power) or 0.0, node))

    elif stage == "retention":
        for node, nr in rec.nodes.items():
            if nr.retention is None:
                continue
            out.append(Pair("retention", rule_retention(nr.retain_power or 0.0, nr.pull_power or 0.0), nr.retention, node))

    elif stage == "current_value":
        for node, nr in rec.nodes.items():
            if nr.current is None or nr.retention is None:
                continue
            cur, outg = rule_current_outgoing(_gross_recorded(world, node), nr.retention)
            out.append(Pair("current", cur, nr.current, node))
            out.append(Pair("outgoing", outg, nr.outgoing or 0.0, node))

    elif stage == "steer_weights":
        observed = identify_observed(world)
        steerers_by_node: dict[str, list[tuple[int, float, float | None]]] = defaultdict(list)
        for (node, tag), e in inp.entries.items():
            r = rec.entries[(node, tag)]
            if e.steering:
                steerers_by_node[node].append((e.steer_link, rule_effective_power(r.val or 0.0, e.t_out, e.t_in), observed.steering_strength.get(tag)))
        for node, nr in rec.nodes.items():
            targets = graph.outgoing(node)
            if not targets or not nr.steer_weights:
                continue
            pred = rule_steer_weights(len(targets), steerers_by_node.get(node, []))
            for i, (p, rv) in enumerate(zip(pred, nr.steer_weights)):
                out.append(Pair(f"steer_weight[{i}]", p, rv, node))

    elif stage == "link_flow":
        adds_by_node: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for (node, _tag), e in inp.entries.items():
            if e.add is not None:
                adds_by_node[node].append((e.steer_link, e.add))
        for node, nr in rec.nodes.items():
            targets = graph.outgoing(node)
            if not targets or nr.outgoing is None or not nr.steer_weights:
                continue
            pred = rule_link_values(nr.outgoing, nr.steer_weights, rule_link_adds(len(targets), adds_by_node.get(node, [])))
            for target, p in zip(targets, pred):
                got = sum(v for src, v, _a in rec.nodes[target].incoming if src == node) if target in rec.nodes else 0.0
                out.append(Pair(f"link_value->{target}", p, got, node))

    elif stage == "income_share":
        for (node, tag), r in rec.entries.items():
            if r.share_total is None or r.val is None:
                continue
            e, nr = inp.entries[(node, tag)], rec.nodes[node]
            eff = rule_effective_power(r.val, e.t_out, e.t_in)
            fraction = rule_power_fraction(eff, nr.retain_power or 0.0)
            if r.power_fraction is not None:
                out.append(Pair("power_fraction", fraction, r.power_fraction, node, tag))
            out.append(Pair("share_total", rule_income_share(nr.current or 0.0, fraction), r.share_total, node, tag))

    elif stage == "income_efficiency":
        observed = identify_observed(world)
        for (node, tag), r in rec.entries.items():
            e = inp.entries[(node, tag)]
            if r.money is None or r.share_total is None or e.has_capital or tag not in observed.trade_efficiency:
                continue
            out.append(Pair("money", rule_money(r.share_total, observed.trade_efficiency[tag], rule_merchant_bonus(e.has_trader)), r.money, node, tag))

    else:
        raise ValueError(f"unknown stage {stage}")
    return out
