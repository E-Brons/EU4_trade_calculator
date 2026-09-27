"""Pydantic request/response models for the API, plus conversion helpers
to/from the plain-dataclass engine types (engine/model.py, engine/optimize.py)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.engine.model import Allocation, MerchantAction, NodeAllocation, NodeState, Params
from app.engine.optimize import MarginalValue, OptimizeConfig, OptimizeResult
from app.engine.simulate import NodeBreakdown, SimulationResult


class NodeStateIn(BaseModel):
    node_id: str
    local_value: float = 0.0
    is_home: bool = False
    player_base_power: float = 0.0
    other_collect_power: float = 0.0
    other_steer_power: dict[str, float] = Field(default_factory=dict)
    other_steer_merchants: dict[str, int] = Field(default_factory=dict)
    other_passive_power: float = 0.0

    def to_engine(self) -> NodeState:
        return NodeState(**self.model_dump())


class NodeAllocationIn(BaseModel):
    merchant_action: MerchantAction = MerchantAction.NONE
    steer_target: str | None = None
    light_ships: int = 0

    def to_engine(self) -> NodeAllocation:
        return NodeAllocation(self.merchant_action, self.steer_target, self.light_ships)


class ParamsIn(BaseModel):
    trade_efficiency: float = 0.0
    merchant_power: float = 2.0
    capital_merchant_power: float = 5.0
    power_per_light_ship: float = 3.0
    home_power_bonus: float = 0.1
    merchant_present_income_bonus: float = 0.1
    steer_value_bonus_per_merchant: float = 0.05
    ship_chunk: int = 5

    def to_engine(self) -> Params:
        return Params(**self.model_dump())


class SimulateRequest(BaseModel):
    node_states: dict[str, NodeStateIn]
    allocation: dict[str, NodeAllocationIn] = Field(default_factory=dict)
    params: ParamsIn = Field(default_factory=ParamsIn)


class NodeBreakdownOut(BaseModel):
    node_id: str
    display_name: str
    local_value: float
    total_value: float
    player_power: float
    total_power: float
    player_collects: bool
    player_income: float
    forwarded_value: float
    link_values: dict[str, float]

    @classmethod
    def from_engine(cls, b: NodeBreakdown, display_name: str) -> "NodeBreakdownOut":
        return cls(display_name=display_name, **b.__dict__)


class SimulateResponse(BaseModel):
    total_income: float
    nodes: dict[str, NodeBreakdownOut]

    @classmethod
    def from_engine(cls, result: SimulationResult, display_names: dict[str, str]) -> "SimulateResponse":
        return cls(
            total_income=result.total_income,
            nodes={
                nid: NodeBreakdownOut.from_engine(b, display_names.get(nid, nid))
                for nid, b in result.nodes.items()
            },
        )


class OptimizeRequest(BaseModel):
    node_states: dict[str, NodeStateIn]
    params: ParamsIn = Field(default_factory=ParamsIn)
    home_node: str
    candidate_nodes: list[str] | None = None  # defaults to all keys in node_states
    max_merchants: int
    max_light_ships: int
    current_allocation: dict[str, NodeAllocationIn] | None = None
    random_seed: int = 0
    max_restarts: int = 3

    def to_engine_config(self) -> OptimizeConfig:
        candidates = self.candidate_nodes if self.candidate_nodes is not None else list(self.node_states.keys())
        return OptimizeConfig(
            home_node=self.home_node,
            candidate_nodes=candidates,
            max_merchants=self.max_merchants,
            max_light_ships=self.max_light_ships,
            random_seed=self.random_seed,
            max_restarts=self.max_restarts,
        )


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

    @classmethod
    def from_engine(cls, m: MarginalValue) -> "MarginalValueOut":
        return cls(**m.__dict__)


class OptimizeResponse(BaseModel):
    income: float
    baseline_income: float
    current_income: float | None
    income_gain_vs_current: float | None
    recommended_actions: list[RecommendedAction]
    merchant_marginals: list[MarginalValueOut]
    ship_marginals: list[MarginalValueOut]
    breakdown: SimulateResponse

    @classmethod
    def from_engine(
        cls,
        result: OptimizeResult,
        display_names: dict[str, str],
        breakdown: SimulationResult,
        current_income: float | None,
    ) -> "OptimizeResponse":
        actions = [
            RecommendedAction(
                node_id=nid,
                display_name=display_names.get(nid, nid),
                merchant_action=a.merchant_action,
                steer_target=a.steer_target,
                steer_target_display_name=display_names.get(a.steer_target) if a.steer_target else None,
                light_ships=a.light_ships,
            )
            for nid, a in result.allocation.nodes.items()
            if a.merchant_action != MerchantAction.NONE or a.light_ships > 0
        ]
        return cls(
            income=result.income,
            baseline_income=result.baseline_income,
            current_income=current_income,
            income_gain_vs_current=(result.income - current_income) if current_income is not None else None,
            recommended_actions=actions,
            merchant_marginals=[MarginalValueOut.from_engine(m) for m in result.merchant_marginals],
            ship_marginals=[MarginalValueOut.from_engine(m) for m in result.ship_marginals],
            breakdown=SimulateResponse.from_engine(breakdown, display_names),
        )


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
    player_tag: str
    warnings: list[str]
    node_states: dict[str, NodeStateIn]
    current_allocation: dict[str, NodeAllocationIn]
    suggested_home_node: str | None
    suggested_trade_efficiency: float | None
    actual_current_income: float
