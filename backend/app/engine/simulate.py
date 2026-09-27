"""Propagates trade value through the node graph and computes the player's
trade income under a given allocation.

This implements EU4's real trade formula, reverse-engineered and verified
against a real melted 1.37.5 save (Ottomans/TUR, home node Constantinople;
see backend/scripts/inspect_save.py and the real save at
`~/Downloads/Ottomans_Ironman_Backup_melted.eu4`). Summary of how it works,
and what was verified:

1. Each node's total value = its own local production value, plus whatever
   value flowed in from upstream nodes (`NodeState.local_value` +
   incoming). Verified directly: for every inspected node, the sum of the
   `top_power_values` of *all* countries present (collectors, steerers,
   and merely-passive countries alike) equals the node's `total` field
   exactly (e.g. constantinople: 778.215+21.152+2.742 = 802.109 = `total`;
   basra and aleppo check out the same way to 3 decimals). This confirms
   the save's per-country `val`/`top_power_values` figures are already
   this node's total value distributed in proportion to trade power --
   i.e. "trade power share of the node" and "ducat share of the node's
   value" are the same ratio, which is exactly what letting `NodeState`'s
   power fields double as value-weights (as `build_node_states_from_save`
   already does for other countries) assumes.

2. Retention: the fraction of a node's total value that stays *in* the
   node (available to whoever collects there) rather than being forwarded
   downstream equals retained power / total power in the node --
   `retention` (a field the save reports directly) matches
   `retain_power / total` to within display rounding on every inspected
   node (constantinople 778.215/802.109=0.9702 vs reported 0.971; basra
   83.474/467.948=0.1791 vs 0.18; aleppo 32.844/646.072=0.0508 vs 0.051;
   ragusa 149.439/600.887=0.2487 vs 0.249). This is exactly the
   power-weighted retained/forwarded split already implemented below.

3. Everything not collected is forwarded down the node's outgoing links,
   split in proportion to steering power (merchants explicitly set to
   Steer); power with no merchant present (in a non-home node) is
   "passive" and follows the same proportions, or splits evenly if nobody
   is steering at all (an edge case with no recoverable real data --
   documented approximation of last resort, see Params docstring).

4. Value moving down a link gets a further bonus of
   `steer_value_bonus_per_merchant` (TRADE_ADDED_VALUE_MODIFER = 0.05 in
   vanilla) per merchant steering that link.

5. The final ducat conversion for the player's own realized income at a
   node they collect at is:

       income = value_share * (1 + trade_efficiency + merchant_present_bonus)

   where `value_share = total_value * player_power / total_power` (the
   power-weighted share from step 2), `trade_efficiency` is
   country-specific and can't be derived here (see Params), and
   `merchant_present_bonus` (TRADE_MERCHANT_PRESENT = 0.1) applies only
   when collecting via an explicitly-stationed merchant. This exact
   two-term additive stack (not a multiplicative 1.1x) was confirmed from
   the real save: TUR's home node (automatic capital collection, no
   merchant present) realizes money at *1.750x* its power-weighted value
   share; TUR's `ragusa` and `venice` nodes (merchant present, collecting
   away from home) realize *1.8498x* and *1.8500x* respectively -- a
   difference of +0.10 (matching TRADE_MERCHANT_PRESENT exactly), landing
   on the additive stack. Back-solving the home ratio gives this specific
   save's trade_efficiency = 0.75 (used only for the end-to-end save
   validation, not as a library default -- see Params.trade_efficiency).

6. Trade power itself = `NodeState.player_base_power` (from the save's
   province_power/ship_power, or manual entry -- already includes
   whatever home-node power bonus the game itself applied) plus, for
   power the player is actively deciding on right now: ship power
   (sea/coastal nodes only) and merchant power (`capital_merchant_power`
   at the home node, `merchant_power` elsewhere) -- with
   TRADE_POWER_HOME_BONUS (+10%) applied to *that added amount* at the
   home node (not to the base, to avoid double-counting a bonus the save
   already baked into province_power).

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
            # A steer target that doesn't exist (missing, stale, or -- from
            # imperfectly reconstructed save data -- simply unknown) would
            # otherwise make this power vanish from both the retained and
            # forwarded totals. Fall back to passive rather than losing value.
            steer_target = None
            player_passive = True

        total_value = state.local_value + incoming_value[node_id]

        total_power = (
            player_power
            + state.other_collect_power
            + sum(state.other_steer_power.values())
            + state.other_passive_power
        )

        retained_power = state.other_collect_power + (player_power if player_collects else 0.0)
        player_share = (player_power / total_power) if (player_collects and total_power > 0) else 0.0

        # TRADE_MERCHANT_PRESENT: +10% income, additive with trade
        # efficiency, only when collecting via an explicitly-stationed
        # merchant (any node, including home) -- not for automatic
        # capital collection with no merchant. See module docstring for
        # how this was confirmed against the real save.
        merchant_present_bonus = params.merchant_present_income_bonus if action == MerchantAction.COLLECT else 0.0
        player_income = 0.0
        if player_collects and total_power > 0:
            player_income = total_value * player_share * (1 + params.trade_efficiency + merchant_present_bonus)

        forwarded_value = max(total_value * (1 - retained_power / total_power), 0.0) if total_power > 0 else total_value

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
    """Player's total trade power at this node: the save/manual-entry
    base power, plus whatever the player is actively deciding to add
    right now (ships, merchant). TRADE_POWER_HOME_BONUS (+10%) applies
    only to that *added* amount at the home node -- the base power at
    home already reflects this bonus in the save's own province_power, so
    applying it again to the base would double-count it (see Params
    docstring)."""
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
