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

from dataclasses import astuple, dataclass, field

from app.engine.model import Allocation, MerchantAction, NodeAllocation, NodeState, Params
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
    # --- Explanatory extras (additive; derived from the same variables as above) ---
    # Fraction of total_value the player captures when collecting here, else 0.
    player_share: float = 0.0
    # The factor actually applied to value*share: 1 + trade_efficiency
    # (+ merchant-present bonus for an explicit Collect). 1.0 when not collecting.
    income_multiplier: float = 1.0
    # Power of every collector at the node (incl. the player if collecting) /
    # power of everyone not collecting (steerers + passive, incl. the player
    # if not collecting). retained_power + pull_power == total_power.
    retained_power: float = 0.0
    pull_power: float = 0.0
    # Value collected at this node by all collectors = total_value - forwarded_value.
    retained_value: float = 0.0
    # What the player is doing here: 'collect' (explicit merchant collecting),
    # 'steer' (merchant steering to player_steer_target), 'passive-home' (no
    # merchant, but home node => auto-collects), 'none' (passive, forwards).
    player_action: str = "none"
    player_steer_target: str | None = None
    player_light_ships: int = 0
    # total_value - local_value, clamped >= 0 (value arriving from upstream).
    incoming_value: float = 0.0
    # True when this node used the save's own recorded numbers (exact replay).
    is_replay: bool = False


@dataclass
class SimulationResult:
    total_income: float
    nodes: dict[str, NodeBreakdown] = field(default_factory=dict)
    # Modelled value flowing INTO each node (sum of upstream link values).
    incoming: dict[str, float] = field(default_factory=dict)


class ReferencedStates(dict):
    """`node_states` plus its precomputed reference incoming flow (see
    `reference_incoming`). Lets a caller that simulates many allocations
    (the optimizer) pay for the reference pass once; `simulate()` picks the
    cached flow up automatically and recomputes if `params` differ."""

    incoming_ref: dict[str, float]
    params_key: tuple


def reference_incoming(
    graph: TradeGraph, node_states: dict[str, NodeState], params: Params
) -> dict[str, float]:
    """Modelled incoming value per node when every node replays the allocation
    recorded in its save. Depends only on node_states and params -- it is the
    anchor `simulate` subtracts to turn an allocation change into a delta on
    each node's recorded gross value."""
    recorded = Allocation(
        nodes={
            nid: NodeAllocation(s.known_player_action, s.known_player_steer_target, s.known_player_light_ships)
            for nid, s in node_states.items()
            if s.known_player_action is not None
        }
    )
    return _run(graph, node_states, recorded, params, None).incoming


def with_reference(graph: TradeGraph, node_states: dict[str, NodeState], params: Params) -> ReferencedStates:
    out = ReferencedStates(node_states)
    out.incoming_ref = reference_incoming(graph, node_states, params)
    out.params_key = astuple(params)
    return out


def simulate(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    allocation: Allocation,
    params: Params,
    incoming_ref: dict[str, float] | None = None,
) -> SimulationResult:
    """`incoming_ref` defaults to the cache carried by a `ReferencedStates`,
    else is computed here (one extra pass)."""
    if incoming_ref is None:
        if isinstance(node_states, ReferencedStates) and node_states.params_key == astuple(params):
            incoming_ref = node_states.incoming_ref
        else:
            incoming_ref = reference_incoming(graph, node_states, params)
    return _run(graph, node_states, allocation, params, incoming_ref)


def _run(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    allocation: Allocation,
    params: Params,
    incoming_ref: dict[str, float] | None,
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

        # Anchor on the save's recorded gross value when there is one and shift
        # it by how much the modelled inflow differs from the all-recorded
        # reference (exactly 0 when no upstream node was changed). Without a
        # recorded value (manual entry) fall back to local + modelled inflow.
        # incoming_ref is None only in the reference pass itself (delta 0).
        if state.known_gross_value is not None:
            delta = 0.0 if incoming_ref is None else incoming_value[node_id] - incoming_ref.get(node_id, 0.0)
            total_value = max(state.known_gross_value + delta, 0.0)
        else:
            delta = 0.0
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
            # Recorded forward amount, plus the forwarded share of any upstream delta.
            forward_frac = (1 - retained_power / total_power) if total_power > 0 else 1.0
            forwarded_value = max(state.known_gross_value - state.known_retained_value, 0.0) + delta * forward_frac
            forwarded_value = max(min(forwarded_value, total_value), 0.0)
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

        if action == MerchantAction.COLLECT:
            player_action = "collect"
        elif steer_target is not None:
            player_action = "steer"
        elif player_collects:
            player_action = "passive-home"
        else:
            player_action = "none"

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
            player_share=player_share,
            income_multiplier=(1 + params.trade_efficiency + merchant_present_bonus) if player_collects else 1.0,
            retained_power=retained_power,
            pull_power=max(total_power - retained_power, 0.0),
            retained_value=max(total_value - forwarded_value, 0.0),
            player_action=player_action,
            player_steer_target=steer_target,
            player_light_ships=alloc.light_ships if alloc else 0,
            incoming_value=max(total_value - state.local_value, 0.0),
            is_replay=is_replay,
        )
        total_income += player_income

    return SimulationResult(total_income=total_income, nodes=breakdowns, incoming=incoming_value)


def _player_power(
    node_id: str,
    state: NodeState,
    alloc,
    is_inland: bool,
    params: Params,
) -> float:
    """Player's trade power at this node: base power (from the save or
    manual entry) plus whatever they're actively adding right now (ships,
    merchant), the whole pre-transfer sum demand-scaled by
    `player_max_demand` (CONFIRMED: `val == max_pow * max_demand` for every
    country in a real save -- see ParsedCountryInNode.max_demand), then the
    player's own recorded power transfer in/out applied on top (post-demand,
    like every other country's -- see NodeState.player_t_in/player_t_out)
    -- see docs/implementation.md's "Trade simulation" section.

    Ship contribution prefers the save's own REAL per-ship rate
    (`player_power_per_ship`) over `Params.power_per_light_ship`, falling
    back to the guess only when there are currently no ships to derive a
    rate from. `player_base_power` already includes the save's own real,
    nonzero-even-without-a-merchant `bonus` for whatever action is
    CURRENTLY recorded (see `_player_base_power` in save.py) -- so a
    hypothetical allocation that keeps the SAME merchant presence (most of
    the optimizer's job: ship count, steer target) adds nothing extra here.
    Only an actual CHANGE in merchant presence needs a correction:
    `Params.merchant_power`/`capital_merchant_power` (a guess) when adding
    one where the save had none to read a real bonus from, or subtracting
    the recorded bonus back out when removing one that was there (exact
    for away nodes, confirmed the residual there is ~0 with no merchant in
    287/288 real cases; an approximation at home, where some of that
    recorded bonus may be an automatic capital/idea bonus that doesn't
    actually depend on the merchant and would survive removing it -- not
    separable from the save's numbers alone). TRADE_POWER_HOME_BONUS
    (+10%) only ever applies to a *guessed* component, never a real one
    already reflecting whatever bonuses actually applied."""
    ships = alloc.light_ships if alloc else 0
    action = alloc.merchant_action if alloc else MerchantAction.NONE
    home_multiplier = 1 + params.home_power_bonus if state.is_home else 1.0

    added = 0.0
    if not is_inland:
        if state.player_power_per_ship is not None:
            added += ships * state.player_power_per_ship
        else:
            added += ships * params.power_per_light_ship * home_multiplier
    if action != MerchantAction.NONE:
        if not state.player_recorded_has_trader:
            guess = params.capital_merchant_power if state.is_home else params.merchant_power
            added += guess * home_multiplier
    elif state.player_recorded_has_trader:
        added -= state.player_merchant_bonus

    return (state.player_base_power + added) * state.player_max_demand + state.player_t_in - state.player_t_out


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
