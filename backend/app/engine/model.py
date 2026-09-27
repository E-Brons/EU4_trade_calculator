"""Core data model for the trade simulation & optimizer.

Everything the player can control is captured in `Allocation`. Everything
about the rest of the world (other countries' trade power, node values) is
captured in `NodeState`, treated as fixed input taken from the save (or the
manual form). `Params` holds the tunable constants that approximate EU4's
real trade formulas -- see engine/simulate.py for how they're used.
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
    """Constants used by the trade formula in simulate.py.

    Reverse-engineered against a real melted 1.37.5 save (Ottomans, home
    node Constantinople; see backend/scripts/inspect_save.py) by comparing
    each trade node's `money` field (the country's actual realized
    ducats/month at that node, taken straight from the game) against the
    node's power-weighted value share. See simulate.py's module docstring
    for the full derivation. Fields below are either a real, named
    defines.lua constant (hardcoded to that exact value) or an explicit,
    documented exception for a genuinely save/country-specific value that
    cannot be derived from the trade block at all.

    One real mechanic that used to be modeled here but was REMOVED because
    the save data refutes it: TRADE_NON_CAPITAL_OFFICE (-0.50) was
    previously applied as a flat 50% trade-power penalty for collecting
    with a merchant away from the home node. The real save has two clean
    counter-examples: TUR collecting away from home at `ragusa`
    (province_power 142.768 -> effective power 149.439, i.e. *higher*, not
    halved) and at `venice` (province_power+ship_power 275.281 -> 268.898,
    a ~2% difference, nowhere near -50%). TRADE_NON_CAPITAL_OFFICE is
    evidently some other, narrower mechanic (most likely tied to a
    specific trade-office building/estate privilege, not ordinary merchant
    collection) and is not applied at all in this model.

    Two important real mechanics that are NOT modeled here, and why:

    - TRADE_PROPAGATE_THRESHOLD (2.0) / TRADE_PROPAGATE_DIVIDER (5):
      confirmed via `basra`'s YEM entry (0.847 power, i.e. below 2.0) that
      a country with less than 2 power in a node is excluded from both
      `retain_power` and `pull_power` -- its tiny value share is simply
      dropped, neither collected nor forwarded. This requires per-country
      granularity (which specific country has <2 power) that isn't
      available at this layer (NodeState only has aggregated buckets by
      role: collect/steer/passive) -- it would need to be filtered in
      save.py's node-state construction, not here. Effect on totals is
      negligible: it only ever concerns minnows contributing a fraction
      of a single node's value (e.g. 1.717 out of basra's total 467.948,
      ~0.37% of that one node).
    - The real default distribution of forwarded value when *nobody* at
      all is steering (an edge case -- in the real save, essentially every
      multi-link node has at least one steering merchant) is not
      recoverable from the data available here (tradenodes.json carries no
      per-link default-weight data). We fall back to an even split across
      outgoing links in that case, which is a documented approximation of
      last resort, not the verified formula used everywhere else.
    """

    # --- Country/save-specific: genuinely cannot be derived here ---
    #
    # Trade Efficiency is a national modifier from trade technology,
    # idea groups (e.g. Economic ideas, trade policies), and some
    # buildings/estate privileges. It is NOT present as a labelled field
    # anywhere in the save's trade={} block. The save's per-country `add`
    # field (docs mentioned it as a candidate) was checked and REFUTED: it
    # only appears on entries that are actively STEERING (never on
    # collectors), and its value (0.092 for TUR across several steering
    # nodes) is inconsistent with the trade efficiency implied by TUR's
    # own realized `money` (~0.75, see simulate.py docstring) -- `add` is
    # something else entirely (most likely an internal steering-value
    # bookkeeping field), not trade efficiency. This must be read off the
    # in-game Economy -> Trade tab (or the country's ledger) and entered
    # by the user; there is nowhere else to get it from a save file.
    trade_efficiency: float = 0.0

    # --- Real, named defines.lua constants ---
    #
    # MERCHANT_MAX_POWER_BONUS: flat trade power added by stationing a
    # merchant at a *non-home* node (collect or steer).
    merchant_power: float = 2.0
    # TRADE_CAPITAL_POWER: flat trade power added by a merchant stationed
    # at the player's *home* node instead of merchant_power (these two
    # don't stack; the capital value replaces the ordinary one).
    capital_merchant_power: float = 5.0
    # TRADE_POWER_HOME_BONUS: +10% multiplier on the trade power the
    # player *adds themselves* (merchant/ships) at the home node. Only
    # applied to that added power, not to `NodeState.player_base_power` --
    # base power at the home node is read straight from the save's
    # province_power, which the game has already computed *with* this
    # bonus applied; re-applying it to the base would double-count it.
    home_power_bonus: float = 0.1
    # TRADE_MERCHANT_PRESENT: +10% bonus to *realized income* (stacks
    # additively with trade_efficiency, applied once as a single combined
    # multiplier -- confirmed against the save: TUR's automatic home-node
    # collection with no merchant realizes exactly (1+trade_efficiency) of
    # its value share, while TUR's merchant-collected nodes away from home
    # realize (1+trade_efficiency+0.1); see simulate.py docstring for the
    # numbers). Applies whenever the player collects via an explicitly
    # stationed merchant (MerchantAction.COLLECT), at *any* node including
    # home -- not when collecting automatically at home with no merchant.
    merchant_present_income_bonus: float = 0.1
    # TRADE_ADDED_VALUE_MODIFER: +5% to the value forwarded down a link,
    # per merchant steering that link (stacks additively per merchant).
    steer_value_bonus_per_merchant: float = 0.05

    # --- Derived from real save data, not a named defines.lua constant ---
    #
    # Light ship base trade power. defines.lua has no single named
    # constant for this (it depends on ship type/naval tech). Derived from
    # the cleanest single-ship data point available (`crimea`: TUR had
    # exactly 1 light ship contributing exactly 3.0 ship_power there).
    # Multi-ship nodes in the same save showed lower per-ship averages
    # (basra: 3.5, venice: ~3.07 for 36 ships), consistent with either ship
    # quality variance or a soft diminishing-returns cap for large stacks
    # that isn't modeled here -- documented approximation for ship-heavy
    # allocations.
    power_per_light_ship: float = 3.0

    # --- Optimizer-only, not a game mechanic ---
    ship_chunk: int = 5  # granularity the optimizer moves ships in
