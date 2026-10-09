"""Pydantic request/response models of the API. The world lives on the server (app/trade/session.py); requests carry
the loaded save's id and the player's decisions, responses describe the result from the player's point of view."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.trade.types import Action, NodeDecision

MerchantAction = Action


class NodeAllocationIn(BaseModel):
    merchant_action: MerchantAction = MerchantAction.NONE
    steer_target: str | None = None
    light_ships: int = 0

    def to_decision(self) -> NodeDecision:
        target = self.steer_target if self.merchant_action == MerchantAction.STEER else None
        return NodeDecision(self.merchant_action, target, self.light_ships)

    @classmethod
    def from_decision(cls, d: NodeDecision) -> "NodeAllocationIn":
        return cls(merchant_action=d.action, steer_target=d.steer_target, light_ships=d.light_ships)


class ParamsIn(BaseModel):
    """The player's scalars the app lets the user change; None = the value identified from the save."""

    trade_efficiency: float | None = None
    power_per_light_ship: float | None = None


class SaveRequest(BaseModel):
    save_id: str
    params: ParamsIn = Field(default_factory=ParamsIn)


class SimulateRequest(SaveRequest):
    allocation: dict[str, NodeAllocationIn] = Field(default_factory=dict)


class NodeBreakdownOut(BaseModel):
    node_id: str
    display_name: str
    local_value: float
    total_value: float                 # gross: local value + everything arriving from upstream
    player_power: float                # the player's effective power here (after transfers)
    total_power: float                 # retained_power + pull_power
    player_collects: bool
    player_income: float
    forwarded_value: float
    link_values: dict[str, float]
    player_share: float = 0.0          # the player's share of the retained value / total_value (before trade efficiency)
    income_multiplier: float = 1.0     # money / share of the retained value (1 + trade efficiency + merchant bonus)
    retained_power: float = 0.0
    pull_power: float = 0.0
    retained_value: float = 0.0
    player_action: str = "none"        # 'collect' | 'steer' | 'passive-home' | 'none'
    player_steer_target: str | None = None
    player_light_ships: int = 0
    incoming_value: float = 0.0
    is_replay: bool = False            # kept for older clients; every value is computed


class SimulateResponse(BaseModel):
    total_income: float
    nodes: dict[str, NodeBreakdownOut]


class NodeOptionsRequest(SimulateRequest):
    node_id: str
    max_light_ships: int = 0


class MerchantOptionOut(BaseModel):
    action: MerchantAction
    steer_target: str | None = None
    steer_target_display_name: str | None = None
    total_income: float
    formula_total_income: float        # = total_income (one calculation); kept for older clients
    is_current: bool
    node: NodeBreakdownOut


class ShipPointOut(BaseModel):
    ships: int
    total_income: float
    formula_total_income: float
    player_power: float
    player_share: float
    node_income: float


class NodeOptionsResponse(BaseModel):
    node_id: str
    display_name: str
    current_total_income: float
    formula_current_total_income: float
    calibration_offset: float = 0.0
    merchant_options: list[MerchantOptionOut]
    ship_curve: list[ShipPointOut]


class OptimizeRequest(SaveRequest):
    home_node: str
    candidate_nodes: list[str] | None = None   # default: the nodes the import suggested
    max_merchants: int
    max_light_ships: int
    current_allocation: dict[str, NodeAllocationIn] | None = None
    random_seed: int = 0
    max_restarts: int = 3


class RecommendedAction(BaseModel):
    node_id: str
    display_name: str
    merchant_action: MerchantAction
    steer_target: str | None
    steer_target_display_name: str | None
    light_ships: int


class MarginalValueOut(BaseModel):
    label: str
    income: float
    delta_vs_optimal: float
    node_id: str | None = None
    node_display_name: str | None = None
    change: str | None = None          # "add" | "remove"
    merchant_action: MerchantAction | None = None
    steer_target: str | None = None
    steer_target_display_name: str | None = None


class OptimizeResponse(BaseModel):
    income: float
    baseline_income: float
    current_income: float | None
    income_gain_vs_current: float | None
    recommended_actions: list[RecommendedAction]
    merchant_marginals: list[MarginalValueOut]
    ship_marginals: list[MarginalValueOut]
    breakdown: SimulateResponse


class TradeNodeOut(BaseModel):
    node_id: str
    display_name: str
    inland: bool
    outgoing: list[str]


class TradeGraphOut(BaseModel):
    game_version: str
    end_nodes: list[str]
    nodes: list[TradeNodeOut]


class ImportSaveResponse(BaseModel):
    save_id: str
    player_tag: str
    date: str
    calc_version: str
    warnings: list[str]
    current_allocation: dict[str, NodeAllocationIn]
    suggested_home_node: str | None
    suggested_trade_efficiency: float | None
    actual_current_income: float       # the player's monthly trade income as the save records it
    suggested_max_merchants: int | None
    suggested_max_light_ships: int | None
    suggested_power_per_light_ship: float | None
    suggested_candidate_nodes: list[str]
