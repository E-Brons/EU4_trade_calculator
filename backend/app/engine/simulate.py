"""Propagates trade value through the node graph and computes the player's
trade income under a given allocation.

The formula and every constant in `Params` are derived from and verified
against 50 real, non-Ironman EU4 saves -- see
`docs/implementation.md`'s "Trade simulation" section for the confirmed
formula, field meanings, and what's still approximate (the replay-vs-
hypothetical distinction below). Don't re-derive or second-guess the shape
of this function without reading that first.

Only the player's own power/behaviour is a variable; every other
country's behaviour is fixed input (`NodeState`), taken from the save or
the manual form.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.model import Allocation, MerchantAction, NodeState, Params
from app.parsing.tradenodes import TradeGraph


@dataclass
class NodeBreakdown:
    node_id: str
    local_value: float
    total_value: float
    player_power: float
    total_power: float
    player_collects: bool
    player_income: float
    forwarded_value: float
    link_values: dict[str, float] = field(default_factory=dict)


@dataclass
class SimulationResult:
    total_income: float
    nodes: dict[str, NodeBreakdown] = field(default_factory=dict)


def simulate(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    allocation: Allocation,
    params: Params,
) -> SimulationResult:
    incoming_value: dict[str, float] = {n: 0.0 for n in graph.nodes}
    breakdowns: dict[str, NodeBreakdown] = {}
    total_income = 0.0

    for node_id in graph.topo_order():
        state = node_states.get(node_id) or NodeState(node_id=node_id)
        alloc = allocation.nodes.get(node_id)
        outgoing = graph.outgoing(node_id)
        action = alloc.merchant_action if alloc else MerchantAction.NONE
        steer_target = alloc.steer_target if (alloc and action == MerchantAction.STEER) else None

        player_power = _player_power(node_id, state, alloc, graph.is_inland(node_id), params)
        player_collects = action == MerchantAction.COLLECT or (action == MerchantAction.NONE and state.is_home)
        player_passive = action == MerchantAction.NONE and not state.is_home

        if action == MerchantAction.STEER and steer_target not in outgoing:
            # Unknown/stale steer target: fall back to passive rather than
            # losing this power from both retained and forwarded totals.
            steer_target = None
            player_passive = True

        total_value = state.local_value + incoming_value[node_id]

        # Replay vs. hypothetical -- see docs/implementation.md's "Trade
        # simulation" section. Only valid when `alloc` matches exactly what
        # the save recorded for this node.
        is_replay = (
            state.matches_recorded(alloc)
            and state.known_retain_power is not None
            and state.known_pull_power is not None
        )

        if is_replay:
            total_value = state.known_gross_value
            retained_power = state.known_retain_power
            total_power = state.known_retain_power + state.known_pull_power
            # Divide by total_power (retain+pull), not retain_power alone --
            # see the confirmed formula in docs/implementation.md.
            player_share = (
                (state.known_player_val / total_power) if (player_collects and total_power > 0) else 0.0
            )
        else:
            total_power = (
                player_power
                + state.other_collect_power
                + sum(state.other_steer_power.values())
                + state.other_passive_power
            )
            retained_power = state.other_collect_power + (player_power if player_collects else 0.0)
            player_share = (player_power / total_power) if (player_collects and total_power > 0) else 0.0

        # TRADE_MERCHANT_PRESENT: additive with trade efficiency, only for
        # an explicitly-stationed collecting merchant (see docs/implementation.md).
        merchant_present_bonus = params.merchant_present_income_bonus if action == MerchantAction.COLLECT else 0.0
        player_income = 0.0
        if player_collects and total_power > 0:
            player_income = total_value * player_share * (1 + params.trade_efficiency + merchant_present_bonus)

        if is_replay:
            forwarded_value = max(total_value - state.known_retained_value, 0.0)
        else:
            forwarded_value = (
                max(total_value * (1 - retained_power / total_power), 0.0) if total_power > 0 else total_value
            )

        link_values = _distribute_forwarded_value(
            total_value=total_value,
            total_power=total_power,
            outgoing=outgoing,
            state=state,
            player_power=player_power,
            player_steer_target=steer_target,
            player_passive=player_passive,
            params=params,
        )
        for target, value in link_values.items():
            incoming_value[target] += value

        breakdowns[node_id] = NodeBreakdown(
            node_id=node_id,
            local_value=state.local_value,
            total_value=total_value,
            player_power=player_power,
            total_power=total_power,
            player_collects=player_collects,
            player_income=player_income,
            forwarded_value=forwarded_value,
            link_values=link_values,
        )
        total_income += player_income

    return SimulationResult(total_income=total_income, nodes=breakdowns)


def _player_power(
    node_id: str,
    state: NodeState,
    alloc,
    is_inland: bool,
    params: Params,
) -> float:
    """Player's trade power at this node: base power (from the save or
    manual entry) plus whatever they're actively adding right now (ships,
    merchant), with the home bonus applied only to the added amount --
    see docs/implementation.md's "Trade simulation" section."""
    ships = alloc.light_ships if alloc else 0
    action = alloc.merchant_action if alloc else MerchantAction.NONE

    added = 0.0
    if not is_inland:
        added += ships * params.power_per_light_ship
    if action != MerchantAction.NONE:
        added += params.capital_merchant_power if state.is_home else params.merchant_power

    if state.is_home:
        added *= 1 + params.home_power_bonus

    return state.player_base_power + added


def _distribute_forwarded_value(
    *,
    total_value: float,
    total_power: float,
    outgoing: tuple[str, ...],
    state: NodeState,
    player_power: float,
    player_steer_target: str | None,
    player_passive: bool,
    params: Params,
) -> dict[str, float]:
    if not outgoing or total_power <= 0:
        return {}

    explicit_weight: dict[str, float] = {t: state.other_steer_power.get(t, 0.0) for t in outgoing}
    if player_steer_target is not None and player_steer_target in explicit_weight:
        explicit_weight[player_steer_target] += player_power

    sum_explicit = sum(explicit_weight.values())

    passive_pool = state.other_passive_power + (player_power if player_passive else 0.0)

    link_weight: dict[str, float] = {}
    for t in outgoing:
        if sum_explicit > 0:
            share = passive_pool * (explicit_weight[t] / sum_explicit)
        else:
            share = passive_pool / len(outgoing)
        link_weight[t] = explicit_weight[t] + share

    values: dict[str, float] = {}
    for t in outgoing:
        base_fraction = link_weight[t] / total_power
        merchants_on_link = state.steer_merchant_count(t) + (1 if t == player_steer_target else 0)
        bonus = 1 + params.steer_value_bonus_per_merchant * merchants_on_link
        values[t] = total_value * base_fraction * bonus
    return values
