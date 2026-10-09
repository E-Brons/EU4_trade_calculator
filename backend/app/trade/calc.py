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
    CountryInput,
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

CALC_VERSION = "0.3.0"
SUPPORTED_GAME_VERSION = game_data.SUPPORTED_GAME_VERSION   # the game version the constants were vendored from

STAGE_INFO: dict[str, tuple[str, tuple[str, ...]]] = {
    "propagation": ("prev = sum over downstream nodes of fx((province_power + ship_power x ship_power_propagation) / TRADE_PROPAGATE_DIVIDER) where that reaches TRADE_PROPAGATE_THRESHOLD", ("R05", "R11")),
    "raw_power": ("max_pow = province + ship + prev + capital + node modifiers + the country's merchant power on every merchant entry", ("R06", "R11")),
    "multiplier": ("max_demand: multiplier from max_pow to val (observed input until derived)", ("R01", "R02")),
    "val": ("val = fx(max_pow * max_demand) (3-decimal fixed point, truncated)", ("R01",)),
    "transfers": ("t_out = fx(f * (val - 0.1)) for a subject giving power away, f = 0.5 or 1.0 identified per giver; t_in = sum of givers' amounts; potential = fx((t_out - t_in) / total)", ("R04",)),
    "retain_power": ("retain_power = sum over collectors of (val - t_out + t_in)", ("R04",)),
    "pull_power": ("pull_power = effective power of the countries that steer here, or do not collect here and collect or steer downstream (R03 rule B)", ("R03", "R04")),
    "retention": ("retention = retain / (retain + pull)", ("R03",)),
    "current_value": ("current = gross * retention; outgoing = gross - current", ("R12",)),
    "steer_weights": ("weight of link i = sum over steerers on link i of effective power x steering strength / sum over all links; strength = TRADE_ADDED_VALUE_MODIFER x (1 + trade_steering)", ("R08",)),
    "steering_bonus": ("add of the steerer ranked r on its link (by effective power x strength) = fx(strength / r) for r <= STEERING_BONUS_RANKS", ("R08",)),
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
    transfer_fraction: dict[str, float] = field(default_factory=dict)
    ship_unit_power: dict[str, float] = field(default_factory=dict)   # override of a country's power per light ship


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

def rule_propagated_power(downstream: Iterable[tuple[float, float]], ship_power_propagation: float) -> float:
    """R05 C-Q2.1/C-Q5.1, R09 C-16: each directly downstream node contributes fx(power / TRADE_PROPAGATE_DIVIDER) when
    that reaches TRADE_PROPAGATE_THRESHOLD, truncated per link. power = province_power + ship_power x the country's
    ship_power_propagation (project check 2026-10-09, 205 clean saves: the +0.75, +3.75, ... left over in the 1618-1789
    saves is ship_power / 4 downstream for countries with Maritime ideas' grand_navy (+0.25), 0 for the others; the
    threshold applies to the sum, e.g. KUT gulf_of_siam (8.99 + 10 x 0.25) / 5 = 2.298). `downstream` = (province_power,
    ship_power) per downstream node."""
    divider, threshold = game_data.const("TRADE_PROPAGATE_DIVIDER"), game_data.const("TRADE_PROPAGATE_THRESHOLD")
    out = 0.0
    for province, ships in downstream:
        p = (province + ships * ship_power_propagation) / divider
        if p >= threshold:
            out += rule_fx(p)
    return out


def rule_propagating_links(stored_weights: tuple[float, ...], link_count: int, steered: bool) -> tuple[bool, ...]:
    """Which outgoing links carry propagated power (R05 open point "which links count", settled 2026-10-09 on the 205
    clean saves: 400,689 of 400,691 entries): every link of a node where some merchant steers; in a node nobody steers
    only the links whose stored weight is above 0 (e.g. cape_of_good_hope -> ivory_coast, weight 0: no prev)."""
    if steered or len(stored_weights) != link_count:
        return (True,) * link_count
    return tuple(w > 0 for w in stored_weights)


def rule_country_modifier(country: CountryInput, name: str) -> float:
    """A country-scope modifier summed over the sources the save names: idea groups (national traditions always, the
    ideas taken in order, the ambition with all seven), policies, government reforms, age abilities, event modifiers,
    the static `navy_tradition` modifier scaled by navy tradition / 100 and `total_blockaded` scaled by the blockaded
    share of ports. Values per source are vendored from the game files (game_data.country_modifier_sources)."""
    src = game_data.country_modifier_sources()
    total = 0.0
    for group, taken in country.idea_groups:
        g = src["idea_groups"].get(group)
        if g:
            total += g["start"].get(name, 0.0) + sum(i.get(name, 0.0) for i in g["ideas"][:taken])
            if taken >= len(g["ideas"]):
                total += g["bonus"].get(name, 0.0)
    for table, keys in (("policies", country.policies), ("government_reforms", country.reforms),
                        ("age_abilities", country.age_abilities), ("event_modifiers", country.modifiers)):
        total += sum(src[table].get(k, {}).get(name, 0.0) for k in keys)
    static = src["static_modifiers"]
    total += static.get("navy_tradition", {}).get(name, 0.0) * country.navy_tradition / 100.0
    total += static.get("total_blockaded", {}).get(name, 0.0) * country.blockaded_percent
    return total


def rule_steering_strength(country: CountryInput) -> float:
    """R08 W-3 with the strength derived instead of identified (project check 2026-10-09): strength =
    TRADE_ADDED_VALUE_MODIFER x (1 + trade_steering). Node weights from it are exact in 8,775 of 9,174 steered
    multi-link nodes of the 205 clean saves (identification from `add` ranks: 4,460); within 5 % in 9,095. The misses
    are later-era countries with a trade_steering source the save does not name per country (estate privileges, trade
    company investments) or navy tradition earned after the month's computation."""
    return game_data.const("TRADE_ADDED_VALUE_MODIFER") * (1.0 + rule_country_modifier(country, "trade_steering"))


def rule_ship_power_propagation(country: CountryInput) -> float:
    return rule_country_modifier(country, "ship_power_propagation")


def rule_fleet_ship_power(ship_types: Iterable[tuple[str, int]]) -> float | None:
    """Power per light ship of a country with no ship on a trade mission: the mean `trade_power` of the light ships in
    its navies (common/units). It leaves out ship trade power modifiers (R11: the deployed ships' ship_power / light_ship
    carries them), so it is only used when no deployed ship shows the real value; None without light ships."""
    known = [(game_data.light_ship_trade_power(t), n) for t, n in ship_types if t in game_data.light_ship_types()]
    count = sum(n for _p, n in known)
    return sum(p * n for p, n in known) / count if count else None


def rule_steering_bonus(steerers: list[tuple[float, float]]) -> list[float]:
    """R08 W-2 + project check 2026-10-09: the steerers of one link ranked by effective power x strength; the one at
    rank r gets add = fx(strength / r) for r <= STEERING_BONUS_RANKS, the rest none (per-link sum of `add` exact in
    18,184 of 19,086 links). `steerers` = (effective power, strength); returns the add of each, in the given order."""
    order = sorted((i for i, (eff, _s) in enumerate(steerers) if eff > 0), key=lambda i: -steerers[i][0] * steerers[i][1])
    adds = [0.0] * len(steerers)
    for rank, i in enumerate(order[:int(game_data.const("STEERING_BONUS_RANKS"))], 1):
        adds[i] = rule_fx(steerers[i][1] / rank)
    return adds


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
    """R10 value/flow analysis 2026-10-08: entries with negative max_pow store no val (109 of 109) and the node
    counts them as 0 (U10 ethiopia: recorded pull 70.297 = 58.844 + 3.381 + 8.072 without them)."""
    return max(0.0, rule_fx(max_pow * multiplier))


def rule_transfer_out(val: float, fraction: float | None = None) -> float:
    """R04: a subject gives fx(fraction * (val - TRANSFER_MIN_POWER_KEPT)). fraction is TRANSFER_FRACTION (0.5; 1,855 of
    1,855 givers of the 80-save corpus) or TRANSFER_FRACTION_FULL (1.0; the plain vassals AVR, LDU of the Venice series);
    what selects it is open, so the giver's fraction is identified from its recorded t_out (rule_transfer_fraction)."""
    f = game_data.const("TRANSFER_FRACTION") if fraction is None else fraction
    return rule_fx(f * (val - game_data.const("TRANSFER_MIN_POWER_KEPT")))


def rule_transfer_fraction(val: float, t_out: float) -> float | None:
    """The known fraction that reproduces a recorded t_out exactly (None if neither does)."""
    for f in (game_data.const("TRANSFER_FRACTION"), game_data.const("TRANSFER_FRACTION_FULL")):
        if abs(rule_transfer_out(val, f) - t_out) < 5e-4:
            return f
    return None


def rule_potential(t_out: float, t_in: float, node_total: float) -> float:
    """R04 + project check (2,991 of 2,991): potential = fx((t_out - t_in) / total), positive for givers, negative for receivers."""
    return rule_fx((t_out - t_in) / node_total) if node_total > 0 else 0.0


def rule_effective_power(val: float, t_out: float, t_in: float) -> float:
    return val - t_out + t_in


def rule_is_collecting(entry: EntryInput, decision: NodeDecision) -> bool:
    """A country collects where its merchant collects and at its home node, unless its merchant steers there (U189/U190,
    VEN's trade port moved to ragusa: the steering merchant at the new home node leaves ragusa's retain_power unchanged
    and its power counts as pull)."""
    return decision.action == Action.COLLECT or (entry.has_capital and decision.action != Action.STEER)


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


def rule_current_outgoing(gross: float, retention: float, weights: tuple[float, ...] = (1.0,)) -> tuple[float, float]:
    """current = gross * retention; outgoing = the rest. Where every link weight is 0 (nobody steers and nobody ever
    has: stored weights 0) nothing leaves and the node keeps its whole value (1,329 of 1,329 node-saves, e.g.
    australia: retention 0.945 recorded, current = gross, no outgoing); so does an end node (no links: genua keeps all
    its value although its pull_power is not 0)."""
    if not any(weights):
        return gross, 0.0
    current = gross * retention
    return current, gross - current


def rule_steer_weights(link_count: int, steerers: Iterable[tuple[int, float, float]],
                       stored: tuple[float, ...] = ()) -> tuple[float, ...]:
    """R08 response_1 W-3: weight of link i = sum over the steering merchants on link i of effective power x the
    country's steering strength (rule_steering_strength), divided by the same sum over all links. Passive pullers and
    collectors do not count. R08 V3-R08-1 (228 unsteered node-saves, 17 clean saves): where no merchant steers the game
    keeps the stored weights (unchanged month to month 140/140, equal to the bookmark values 84/84), so they are
    returned as they are. A single steered link carries everything. The weights are stored and applied in fixed point
    (they sum to 0.998-1.000; full precision forwarded ~0.1 % too much value per hop, 2026-10-09)."""
    steerers = [s for s in steerers if s[1] != 0]
    if not steerers and len(stored) == link_count:
        return tuple(stored)
    if link_count == 1:
        return (1.0,)
    per_link = [0.0] * link_count
    for link, power, strength in steerers:
        if link < link_count:
            per_link[link] += power * strength
    total = sum(per_link)
    if total > 0:
        return tuple(rule_fx(p / total) for p in per_link)
    if len(stored) == link_count:  # steerers present but all with strength 0: nothing steers, the stored weights stay
        return tuple(stored)
    return tuple(math.nan for _ in per_link)


def rule_link_adds(link_count: int, adds: Iterable[tuple[int, float]]) -> tuple[float, ...]:
    """Sum of the `add` of every entry with that key, per steered link (R08 C-05: the key, not `type`, marks it)."""
    per_link = [0.0] * link_count
    for link, add in adds:
        if link < link_count:
            per_link[link] += add
    return tuple(per_link)


def rule_link_values(outgoing: float, weights: tuple[float, ...], link_adds: tuple[float, ...]) -> tuple[float, ...]:
    """R08 C-06 (12,590 of 12,590 links): value on link i = outgoing * weight_i * (1 + sum of `add` on link i); the
    bonus is value created on the link."""
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

def ship_unit_power(inputs: WorldInputs, observed: Observed) -> dict[str, float]:
    """Trade power of one more light ship per country: the save's ship_power / light_ship (R11), unless given."""
    ships: dict[str, int] = defaultdict(int)
    power: dict[str, float] = defaultdict(float)
    for e in inputs.entries.values():
        ships[e.tag] += e.light_ships
        power[e.tag] += e.ship_power
    out = {t: power[t] / n for t, n in ships.items() if n > 0}
    if inputs.player not in out:
        fleet = rule_fleet_ship_power(inputs.player_ship_types)
        if fleet is not None:
            out[inputs.player] = fleet
    return out | dict(observed.ship_unit_power)


@lru_cache(maxsize=1)
def _upstream() -> dict[str, tuple[str, ...]]:
    graph = game_data.graph()
    up: dict[str, list[str]] = defaultdict(list)
    for node in graph.nodes:
        for target in graph.outgoing(node):
            up[target].append(node)
    return {n: tuple(v) for n, v in up.items()}


def _country(inputs: WorldInputs, tag: str, needed_for: str) -> CountryInput:
    country = inputs.countries.get(tag)
    if country is None:
        raise UnknownVariable("country modifiers", f"{tag} ({needed_for})", "R08")
    return country


@dataclass
class _Row:
    """One country at one node after the power stages: what the node stages need."""

    e: EntryInput
    eff: float
    collecting: bool
    steering: bool
    link: int
    pulling: bool = False


class _Context:
    """Per-calculation lookups shared by the entry and node passes (ship power, ship propagation, steering strength)."""

    def __init__(self, inputs: WorldInputs, decisions: Decisions, observed: Observed):
        self.inputs, self.decisions, self.observed = inputs, decisions, observed
        self.unit_power = ship_unit_power(inputs, observed)
        self._propagation: dict[str, float] = {}
        self._strength: dict[str, float] = {}

    def ship_power(self, e: EntryInput, d: NodeDecision) -> float:
        if not d.light_ships:
            return 0.0
        if d.light_ships == e.light_ships and e.ship_power > 0:
            return e.ship_power   # unchanged: the save's own ship power (per-node ship modifiers included)
        if e.tag in self.unit_power:
            return d.light_ships * self.unit_power[e.tag]
        raise UnknownVariable("ship unit power", f"{e.tag}@{e.node}", "R11")

    def propagation(self, tag: str) -> float:
        if tag not in self._propagation:
            self._propagation[tag] = rule_ship_power_propagation(_country(self.inputs, tag, "ship power propagation"))
        return self._propagation[tag]

    def strength(self, tag: str) -> float:
        if tag not in self._strength:
            self._strength[tag] = rule_steering_strength(_country(self.inputs, tag, "steering strength"))
        return self._strength[tag]


def _entry_rows(ctx: _Context, node: str, node_entries: Iterable[EntryInput], ship_power: dict[tuple[str, str], float],
                steered: bool, results: dict[tuple[str, str], EntryResult]) -> list[_Row]:
    """Power stages for the entries of one node: propagation, raw power, val, transfers (all node-local: a transfer
    goes to a receiver in the same node). Fills `results`; `pulling` is set later (it needs the country's other nodes)."""
    graph, inputs, decisions, observed = game_data.graph(), ctx.inputs, ctx.decisions, ctx.observed
    targets = graph.outgoing(node) if node in graph else ()
    info = inputs.nodes.get(node)
    gate = rule_propagating_links(info.stored_steer_weights if info else (), len(targets), steered)
    first: list[tuple[EntryInput, NodeDecision, float, bool, bool]] = []
    for e in node_entries:
        tag = e.tag
        d = decisions.get(tag, node)
        downstream = []
        for down, g in zip(targets, gate):
            if g:
                de = inputs.entries.get((down, tag))
                downstream.append((de.province_power if de else 0.0, ship_power.get((down, tag), 0.0)))
        spp = ctx.propagation(tag) if any(sp for _p, sp in downstream) else 0.0
        prev = rule_propagated_power(downstream, spp)
        merchant_present = d.action != Action.NONE or (e.has_trader and inputs.decisions.get(tag, node).action == Action.NONE)
        if merchant_present and tag not in observed.merchant_power:
            raise UnknownVariable("merchant power", tag, "R06")
        max_pow = rule_max_pow(e.province_power, ship_power.get((node, tag), 0.0), prev,
                               rule_flat_extras(e, observed.merchant_power.get(tag, 0.0) if merchant_present else 0.0))
        multiplier = inputs.multipliers.get((node, tag))
        if multiplier is None and max_pow != 0:
            raise UnknownVariable("max_demand", f"{tag}@{node}", "R01")
        collecting = rule_is_collecting(e, d)
        recorded_away = e.collecting and not e.has_capital
        multiplier = (multiplier or 0.0) * rule_away_adjustment(recorded_away, collecting and not e.has_capital)
        val = rule_val(max_pow, multiplier)
        results[(node, tag)] = EntryResult(prev=prev, max_pow=max_pow, val=val, collecting=collecting)
        first.append((e, d, val, collecting, rule_is_steering(d)))
    # Transfers (R04): a giver's t_out follows its own val; the amounts it sends to each receiver scale with it.
    t_out_now: dict[str, float] = {}
    t_in_delta: dict[str, float] = defaultdict(float)
    for e, _d, val, _c, _s in first:
        if e.t_out > 0:
            new_out = rule_transfer_out(val, observed.transfer_fraction.get(e.tag))
            t_out_now[e.tag] = new_out
            for receiver, amount in e.transfers_to:
                t_in_delta[receiver] += amount * (new_out / e.t_out) - amount
    rows = []
    for e, d, val, collecting, steering in first:
        eff = rule_effective_power(val, t_out_now.get(e.tag, e.t_out), e.t_in + t_in_delta.get(e.tag, 0.0))
        results[(node, e.tag)].effective = eff
        link = targets.index(d.steer_target) if steering and d.steer_target in targets else e.steer_link
        rows.append(_Row(e, eff, collecting, steering, link))
    return rows


def _set_pulling(node_rows: dict[str, list[_Row]], tags: set[str] | None = None) -> None:
    """R03 rule B needs each country's collecting and steering nodes; sets _Row.pulling (only for `tags` if given)."""
    active: dict[str, set[str]] = defaultdict(set)
    for node, rows in node_rows.items():
        for r in rows:
            if (tags is None or r.e.tag in tags) and (r.collecting or r.steering):
                active[r.e.tag].add(node)
    for node, rows in node_rows.items():
        for r in rows:
            if tags is None or r.e.tag in tags:
                r.pulling = rule_is_pulling(node, r.steering, r.collecting, active[r.e.tag])


@dataclass
class _NodePower:
    """What the value stages of one node need from its countries."""

    retain: float = 0.0
    pull: float = 0.0
    steerers: list[tuple[int, float, float]] = field(default_factory=list)   # (link, effective power, strength)


def _node_power(ctx: _Context, rows: Iterable[_Row], into: _NodePower | None = None) -> _NodePower:
    out = into or _NodePower()
    for r in rows:
        if r.collecting:
            out.retain += r.eff
        if r.pulling:
            out.pull += r.eff
        if r.steering and r.eff != 0:
            out.steerers.append((r.link, r.eff, ctx.strength(r.e.tag)))
    return out


def _value_flow(inputs: WorldInputs, power: dict[str, _NodePower]) -> dict[str, NodeResult]:
    """The value stages over the graph in topological order: retention, current/outgoing, weights, bonus, links."""
    graph = game_data.graph()
    results: dict[str, NodeResult] = {}
    incoming: dict[str, float] = defaultdict(float)
    empty = _NodePower()
    for node in graph.topo_order():
        info = inputs.nodes.get(node)
        p = power.get(node, empty)
        gross = (info.local_value if info else 0.0) + incoming[node]
        retention = rule_retention(p.retain, p.pull)
        targets = graph.outgoing(node)
        weights = rule_steer_weights(len(targets), p.steerers, info.stored_steer_weights if info else ())
        current, outgoing = rule_current_outgoing(gross, retention, weights)
        by_link: dict[int, list[tuple[float, float]]] = defaultdict(list)
        for link, eff, strength in p.steerers:
            by_link[link].append((eff, strength))
        link_adds = rule_link_adds(len(targets), [(link, add) for link, group in by_link.items() for add in rule_steering_bonus(group)])
        link_values = rule_link_values(outgoing, weights, link_adds)
        for target, v in zip(targets, link_values):
            incoming[target] += v
        results[node] = NodeResult(gross=gross, retain_power=p.retain, pull_power=p.pull, retention=retention, current=current,
                                   outgoing=outgoing, steer_weights=weights, link_values=dict(zip(targets, link_values)))
    return results


def _money(ctx: _Context, node: NodeResult, row: _Row, result: EntryResult) -> None:
    result.share_total = rule_income_share(node.current, rule_power_fraction(row.eff, node.retain_power))
    if row.e.tag not in ctx.observed.trade_efficiency:
        raise UnknownVariable("trade_efficiency", row.e.tag, "R07")
    result.money = rule_money(result.share_total, ctx.observed.trade_efficiency[row.e.tag], rule_merchant_bonus(row.e.has_trader))


def _with_decided_entries(inputs: WorldInputs, decisions: Decisions, ctx: _Context, tags: set[str] | None = None
                          ) -> tuple[dict[tuple[str, str], EntryInput], dict[tuple[str, str], float]]:
    """Entries (the save's, plus a blank one wherever a decision puts a merchant or ships, plus upstream of ships that
    propagate) and the ship power of each, for every country or only `tags`."""
    entries = {k: e for k, e in inputs.entries.items() if tags is None or k[1] in tags}
    for (tag, node), d in decisions.by_entry.items():
        if (tags is None or tag in tags) and (node, tag) not in entries and (d.action != Action.NONE or d.light_ships):
            entries[(node, tag)] = EntryInput(tag=tag, node=node)
    ship_power = {}
    for (node, tag), e in entries.items():
        sp = ctx.ship_power(e, decisions.get(tag, node))
        if sp:
            ship_power[(node, tag)] = sp
    for (node, tag) in list(ship_power):
        if ctx.propagation(tag):
            for up in _upstream().get(node, ()):   # ships can propagate into a node where the country had nothing
                entries.setdefault((up, tag), EntryInput(tag=tag, node=up))
    return entries, ship_power


def _steered_nodes(decisions: Decisions) -> set[str]:
    return {node for (_tag, node), d in decisions.by_entry.items() if rule_is_steering(d)}


def calculate(inputs: WorldInputs, decisions: Decisions | None = None, observed: Observed | None = None) -> TradeResult:
    """The whole world from raw inputs and every country's decisions."""
    decisions = decisions if decisions is not None else inputs.decisions
    ctx = _Context(inputs, decisions, observed or Observed())
    entries, ship_power = _with_decided_entries(inputs, decisions, ctx)
    steered = _steered_nodes(decisions)
    by_node: dict[str, list[EntryInput]] = defaultdict(list)
    for (node, _tag), e in entries.items():
        by_node[node].append(e)
    entry_results: dict[tuple[str, str], EntryResult] = {}
    node_rows = {node: _entry_rows(ctx, node, es, ship_power, node in steered, entry_results) for node, es in by_node.items()}
    _set_pulling(node_rows)
    nodes = _value_flow(inputs, {node: _node_power(ctx, rows) for node, rows in node_rows.items()})
    for node, rows in node_rows.items():
        for r in rows:
            if r.collecting:
                _money(ctx, nodes[node], r, entry_results[(node, r.e.tag)])
    return TradeResult(entries=entry_results, nodes=nodes)


class WhatIf:
    """calculate() for many alternative decisions of ONE country (the optimizer, the node inspector): everything that
    does not depend on that country's decisions is computed once; each evaluate() recomputes the country's own
    entries, the nodes whose propagation gate it changes, and the value flow. Same rule functions as calculate();
    tests/trade/test_what_if.py checks that both give the same result."""

    def __init__(self, inputs: WorldInputs, observed: Observed, tag: str, base: Decisions | None = None):
        self.inputs, self.observed, self.tag = inputs, observed, tag
        base = base if base is not None else inputs.decisions
        self._others = Decisions({k: d for k, d in base.by_entry.items() if k[0] != tag})
        ctx = _Context(inputs, self._others, observed)
        entries, self._ship_power = _with_decided_entries(inputs, self._others, ctx, {t for _n, t in inputs.entries} - {tag})
        self._steered = _steered_nodes(self._others)
        self._entries: dict[str, list[EntryInput]] = defaultdict(list)
        for (node, _t), e in entries.items():
            self._entries[node].append(e)
        self._results: dict[tuple[str, str], EntryResult] = {}
        self._rows = {node: _entry_rows(ctx, node, es, self._ship_power, node in self._steered, self._results)
                      for node, es in self._entries.items()}
        _set_pulling(self._rows)
        self._power = {node: _node_power(ctx, rows) for node, rows in self._rows.items()}
        self._strength = ctx._strength

    def evaluate(self, decisions: dict[str, NodeDecision]) -> TradeResult:
        """`decisions` = node -> the country's decision there (missing = no merchant, no ships). Returns every node and
        the country's own entries."""
        tag = self.tag
        merged = Decisions(dict(self._others.by_entry) | {(tag, node): d for node, d in decisions.items()})
        ctx = _Context(self.inputs, merged, self.observed)
        ctx._strength = dict(self._strength)
        own, own_ships = _with_decided_entries(self.inputs, Decisions({(tag, n): d for n, d in decisions.items()}), ctx, {tag})
        ship_power = self._ship_power | own_ships
        steered = self._steered | {n for n, d in decisions.items() if rule_is_steering(d)}
        changed_gate = {n for n in steered - self._steered}
        own_by_node: dict[str, list[EntryInput]] = defaultdict(list)
        for (node, _t), e in own.items():
            own_by_node[node].append(e)
        results: dict[tuple[str, str], EntryResult] = {}
        power = dict(self._power)
        rows_of: dict[str, list[_Row]] = {}
        for node in set(own_by_node) | changed_gate:
            own_entries = own_by_node.get(node, [])
            transfers = any(e.t_out or e.t_in for e in own_entries)
            if node in changed_gate or transfers:   # the others' power at this node changes too: recompute the node
                others_results: dict[tuple[str, str], EntryResult] = {}
                rows = _entry_rows(ctx, node, self._entries.get(node, []) + own_entries, ship_power, node in steered, others_results)
                for r in rows:
                    if r.e.tag != tag:
                        r.pulling = next((o.pulling for o in self._rows.get(node, []) if o.e.tag == r.e.tag), False)
                results.update({k: v for k, v in others_results.items() if k[1] == tag})
                rows_of[node] = rows
            else:
                rows_of[node] = _entry_rows(ctx, node, own_entries, ship_power, node in steered, results)
        own_rows = {node: [r for r in rows if r.e.tag == tag] for node, rows in rows_of.items()}
        _set_pulling(own_rows, {tag})
        for node, rows in rows_of.items():
            if node in changed_gate or any(r.e.tag != tag for r in rows):
                power[node] = _node_power(ctx, rows)
            else:
                base = self._power.get(node, _NodePower())
                power[node] = _node_power(ctx, rows, _NodePower(base.retain, base.pull, list(base.steerers)))
        nodes = _value_flow(self.inputs, power)
        for node, rows in own_rows.items():
            for r in rows:
                if r.collecting:
                    _money(ctx, nodes[node], r, results[(node, tag)])
        return TradeResult(entries=results, nodes=nodes)

    def income(self, decisions: dict[str, NodeDecision]) -> float:
        return self.evaluate(decisions).income(self.tag)


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
    # R07/R10 value analysis 2026-10-08: countries whose capital entry records no money (no power there, or a share
    # that truncates to 0) are identified at any other collecting entry with money (most common value); countries with
    # no recorded money anywhere get 0.0 - their share is 0, so the value cannot change any result. Without this the
    # chain stopped in 179 of 205 saves on an unknown trade_efficiency.
    fallback: dict[str, Counter[float]] = defaultdict(Counter)
    for (node, tag), e in world.inputs.entries.items():
        rec = world.recorded.entries.get((node, tag))
        if tag not in efficiency and e.collecting and rec and rec.money and rec.share_total:
            fallback[tag][round(rule_trade_efficiency(rec.money, rec.share_total, rule_merchant_bonus(e.has_trader)), 2)] += 1
    efficiency.update({tag: c.most_common(1)[0][0] for tag, c in fallback.items()})
    for (node, tag), e in world.inputs.entries.items():
        rec = world.recorded.entries.get((node, tag))
        if (e.has_capital or e.collecting) and tag not in efficiency and not (rec and rec.money):
            efficiency[tag] = 0.0
    fractions: dict[str, Counter[float]] = defaultdict(Counter)
    for (node, tag), e in world.inputs.entries.items():
        rec = world.recorded.entries.get((node, tag))
        if e.t_out > 0 and rec and rec.val is not None:
            f = rule_transfer_fraction(rec.val, e.t_out)
            if f is not None:
                fractions[tag][f] += 1
    fraction = {tag: c.most_common(1)[0][0] for tag, c in fractions.items()}
    return Observed(trade_efficiency=efficiency, merchant_power=merchant, transfer_fraction=fraction)


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
        steered = {node for (node, _tag), e in inp.entries.items() if e.steering}
        for (node, tag), r in rec.entries.items():
            targets = graph.outgoing(node) if node in graph else ()
            gate = rule_propagating_links(inp.nodes[node].stored_steer_weights, len(targets), node in steered)
            downstream = [(inp.entries[(d, tag)].province_power, inp.entries[(d, tag)].ship_power) for d, g in zip(targets, gate)
                          if g and (d, tag) in inp.entries]
            ships = any(sp for _p, sp in downstream)
            spp = rule_ship_power_propagation(inp.countries[tag]) if ships and tag in inp.countries else 0.0
            out.append(Pair("prev", rule_propagated_power(downstream, spp), r.prev or 0.0, node, tag))

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
        fraction = identify_observed(world).transfer_fraction
        received: dict[tuple[str, str], float] = defaultdict(float)
        for (node, tag), e in inp.entries.items():
            r = rec.entries[(node, tag)]
            if e.t_out > 0:
                out.append(Pair("t_out", rule_transfer_out(r.val or 0.0, fraction.get(tag)), e.t_out, node, tag))
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
            cur, outg = rule_current_outgoing(_gross_recorded(world, node), nr.retention, nr.steer_weights)
            out.append(Pair("current", cur, nr.current, node))
            out.append(Pair("outgoing", outg, nr.outgoing or 0.0, node))

    elif stage in ("steer_weights", "steering_bonus"):
        strengths = {tag: rule_steering_strength(c) for tag, c in inp.countries.items()}
        steerers_by_node: dict[str, list[tuple[int, float, float, str]]] = defaultdict(list)
        for (node, tag), e in inp.entries.items():
            r = rec.entries[(node, tag)]
            eff = rule_effective_power(r.val or 0.0, e.t_out, e.t_in)
            if e.steering and eff != 0 and tag in strengths:
                steerers_by_node[node].append((e.steer_link, eff, strengths[tag], tag))
        for node, nr in rec.nodes.items():
            targets = graph.outgoing(node) if node in graph else ()
            steerers = steerers_by_node.get(node, [])
            if stage == "steer_weights":
                if not targets or not nr.steer_weights:
                    continue
                pred = rule_steer_weights(len(targets), [s[:3] for s in steerers], inp.nodes[node].stored_steer_weights)
                for i, (p, rv) in enumerate(zip(pred, nr.steer_weights)):
                    out.append(Pair(f"steer_weight[{i}]", p, rv, node))
                continue
            for link in sorted({s[0] for s in steerers}):
                group = [s for s in steerers if s[0] == link]
                pred = sum(rule_steering_bonus([(eff, st) for _l, eff, st, _t in group]))
                recorded = sum(inp.entries[(node, t)].add or 0.0 for _l, _e, _s, t in group)
                out.append(Pair(f"add[{link}]", pred, recorded, node))

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
