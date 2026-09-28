"""Core data model for the trade simulation & optimizer.

Everything the player can control is captured in `Allocation`. Everything
about the rest of the world (other countries' trade power, node values) is
captured in `NodeState`, treated as fixed input taken from the save (or the
manual form). `Params` holds the tunable constants that approximate EU4's
real trade formulas -- see docs/implementation.md's "Trade simulation"
section for the confirmed formula and how these are used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MerchantAction(str, Enum):
    NONE = "none"
    COLLECT = "collect"
    STEER = "steer"


@dataclass
class NodeState:
    """Everything about a node that the player does NOT control directly:
    the node's own production value and the trade power/behaviour of every
    other country present in it."""

    node_id: str
    local_value: float = 0.0
    is_home: bool = False

    # The player's trade power that exists in this node regardless of
    # merchant/ship allocation (from owning provinces there).
    player_base_power: float = 0.0

    # Aggregate trade power of every OTHER country that collects here.
    other_collect_power: float = 0.0
    # Aggregate trade power of every OTHER country steering toward each
    # downstream node (keyed by target node id).
    other_steer_power: dict[str, float] = field(default_factory=dict)
    # Number of other countries' merchants steering toward each target,
    # used for the +5%/merchant steering value bonus. Defaults to 1 per
    # link that has any steer power, if not given explicitly.
    other_steer_merchants: dict[str, int] = field(default_factory=dict)
    # Trade power present but not committed to collect or steer (no
    # merchant there, and not that country's home node). Gets forwarded
    # in proportion to the explicit steering (or evenly if none).
    other_passive_power: float = 0.0

    # --- Authoritative save data, when this NodeState was built from a real
    # save rather than manual entry -- only valid for an exact replay of
    # the save's own recorded allocation (see matches_recorded and
    # docs/implementation.md's "Trade simulation" section).
    known_gross_value: float | None = None  # local_value + sum(incoming[].value), read directly
    known_retained_value: float | None = None  # the save's own `current` field
    known_retain_power: float | None = None
    known_pull_power: float | None = None
    known_player_val: float = 0.0  # the player's own `val` field at this node, as recorded
    known_player_action: MerchantAction | None = None
    known_player_light_ships: int = 0
    known_player_steer_target: str | None = None

    def matches_recorded(self, alloc: NodeAllocation | None) -> bool:
        """True iff `alloc` is exactly what was recorded for this node in the
        save this NodeState came from -- the only case where the known_*
        fields above are valid to use as-is."""
        if self.known_player_action is None:
            return False
        recorded = NodeAllocation(
            merchant_action=self.known_player_action,
            steer_target=self.known_player_steer_target,
            light_ships=self.known_player_light_ships,
        )
        given = alloc if alloc is not None else NodeAllocation()
        return given.key() == recorded.key()

    def steer_merchant_count(self, target: str) -> int:
        if target in self.other_steer_merchants:
            return self.other_steer_merchants[target]
        return 1 if self.other_steer_power.get(target, 0.0) > 0 else 0


@dataclass
class NodeAllocation:
    """What the player is doing at one node."""

    merchant_action: MerchantAction = MerchantAction.NONE
    steer_target: str | None = None  # required iff merchant_action == STEER
    light_ships: int = 0

    def key(self) -> tuple:
        return (self.merchant_action.value, self.steer_target, self.light_ships)


@dataclass
class Allocation:
    """The full set of the player's decisions across all candidate nodes."""

    nodes: dict[str, NodeAllocation] = field(default_factory=dict)

    def get(self, node_id: str) -> NodeAllocation:
        return self.nodes.setdefault(node_id, NodeAllocation())

    def merchant_count(self) -> int:
        return sum(
            1
            for a in self.nodes.values()
            if a.merchant_action != MerchantAction.NONE
        )

    def light_ship_count(self) -> int:
        return sum(a.light_ships for a in self.nodes.values())

    def copy(self) -> "Allocation":
        return Allocation(
            nodes={
                nid: NodeAllocation(a.merchant_action, a.steer_target, a.light_ships)
                for nid, a in self.nodes.items()
            }
        )


@dataclass
class Params:
    """Constants used by the trade formula in simulate.py. Each is either a
    real, named `defines.lua` constant or an explicit, documented exception
    for a value that can't be derived from a save at all -- see
    docs/implementation.md's "Trade simulation" section for the derivation,
    confirmed/refuted mechanics, and known approximations (the `<2.0`-power
    propagation threshold, and the even-split fallback when nobody at all
    is steering out of a node)."""

    # Trade Efficiency: a national modifier (tech/ideas/buildings) not
    # present as a labelled field anywhere in the trade block -- must be
    # read off the in-game Economy -> Trade tab and entered by the user.
    trade_efficiency: float = 0.0

    # MERCHANT_MAX_POWER_BONUS: flat trade power added by a merchant at a
    # *non-home* node (collect or steer).
    merchant_power: float = 2.0
    # TRADE_CAPITAL_POWER: same, but at the player's *home* node (doesn't
    # stack with merchant_power -- this replaces it there).
    capital_merchant_power: float = 5.0
    # TRADE_POWER_HOME_BONUS: +10% multiplier on trade power the player
    # *adds themselves* at the home node (not the save-provided base,
    # which already includes it).
    home_power_bonus: float = 0.1
    # TRADE_MERCHANT_PRESENT: +10% additive income bonus for collecting via
    # an explicitly-stationed merchant, at any node.
    merchant_present_income_bonus: float = 0.1
    # TRADE_ADDED_VALUE_MODIFER: +5% to value forwarded down a link, per
    # merchant steering that link (stacks additively).
    steer_value_bonus_per_merchant: float = 0.05

    # Light ship base trade power -- not a single named defines.lua
    # constant (depends on ship type/tech); derived from the cleanest
    # single-ship real save data point available.
    power_per_light_ship: float = 3.0

    # --- Optimizer-only, not a game mechanic ---
    ship_chunk: int = 5  # granularity the optimizer moves ships in
