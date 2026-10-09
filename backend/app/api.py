"""API routes: trade node graph, save import, simulate, node options, optimize. Every number comes from
app/trade/calc.py (the calculation the verifier checks against real saves) for the save loaded by /api/import-save."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.parsing import ironman_melt
from app.parsing.tradenodes import TradeGraph, load_trade_graph
from app.schemas import (
    ImportSaveResponse,
    MarginalValueOut,
    MerchantOptionOut,
    NodeAllocationIn,
    NodeBreakdownOut,
    NodeOptionsRequest,
    NodeOptionsResponse,
    OptimizeRequest,
    OptimizeResponse,
    RecommendedAction,
    ShipPointOut,
    SimulateRequest,
    SimulateResponse,
    TradeGraphOut,
    TradeNodeOut,
)
from app.trade import calc, session as sessions
from app.trade.optimize import Marginal, OptimizeConfig, optimize
from app.trade.session import Session
from app.trade.types import Action, NodeDecision, TradeResult, UnknownVariable

router = APIRouter(prefix="/api")

SHIP_CURVE_MAX = 150


@router.get("/tradenodes", response_model=TradeGraphOut)
def get_tradenodes() -> TradeGraphOut:
    graph = load_trade_graph()
    return TradeGraphOut(
        game_version=graph.game_version,
        end_nodes=graph.end_nodes,
        nodes=[TradeNodeOut(node_id=i.node_id, display_name=i.display_name, inland=i.inland, outgoing=list(i.outgoing))
               for i in graph.nodes.values()],
    )


def _session(save_id: str) -> Session:
    s = sessions.get(save_id)
    if s is None:
        raise HTTPException(404, "This save is no longer loaded on the server (it was restarted or other saves were loaded "
                                 "since). Upload the save again.")
    return s


def _placement(allocation: dict[str, NodeAllocationIn], graph: TradeGraph) -> dict[str, NodeDecision]:
    unknown = [n for n in allocation if n not in graph]
    if unknown:
        raise HTTPException(422, f"Unknown trade node id(s): {unknown}")
    return {n: a.to_decision() for n, a in allocation.items()}


def _current_placement(s: Session) -> dict[str, NodeDecision]:
    return {node: d for (tag, node), d in s.world.inputs.decisions.by_entry.items() if tag == s.player}


def _home_node(s: Session) -> str | None:
    return next((node for (node, tag), e in s.world.inputs.entries.items() if tag == s.player and e.has_capital), None)


def _evaluate(s: Session, req, placement: dict[str, NodeDecision]) -> TradeResult:
    try:
        return s.what_if(req.params.trade_efficiency, req.params.power_per_light_ship).evaluate(placement)
    except UnknownVariable as e:
        raise HTTPException(422, f"The calculation needs a value this save does not give: {e}") from e


def _breakdown(s: Session, graph: TradeGraph, result: TradeResult, placement: dict[str, NodeDecision], node: str) -> NodeBreakdownOut:
    tag = s.player
    nr = result.nodes[node]
    er = result.entries.get((node, tag))
    e = s.world.inputs.entries.get((node, tag))
    d = placement.get(node, NodeDecision())
    info = s.world.inputs.nodes.get(node)
    local = info.local_value if info else 0.0
    collects = bool(er and er.collecting)
    if d.action == Action.STEER:
        action = "steer"
    elif d.action == Action.COLLECT:
        action = "collect"
    else:
        action = "passive-home" if collects and e is not None and e.has_capital else "none"
    return NodeBreakdownOut(
        node_id=node, display_name=graph.display_name(node), local_value=local, total_value=nr.gross,
        player_power=er.effective if er else 0.0, total_power=nr.retain_power + nr.pull_power,
        player_collects=collects, player_income=er.money if er else 0.0, forwarded_value=nr.outgoing,
        link_values=dict(nr.link_values), player_share=(er.share_total / nr.gross) if er and nr.gross > 0 else 0.0,
        income_multiplier=(er.money / er.share_total) if er and er.share_total > 0 else 1.0,
        retained_power=nr.retain_power, pull_power=nr.pull_power, retained_value=nr.current,
        player_action=action, player_steer_target=d.steer_target, player_light_ships=d.light_ships,
        incoming_value=max(nr.gross - local, 0.0),
    )


def _simulation(s: Session, graph: TradeGraph, result: TradeResult, placement: dict[str, NodeDecision]) -> SimulateResponse:
    return SimulateResponse(total_income=result.income(s.player),
                            nodes={n: _breakdown(s, graph, result, placement, n) for n in result.nodes})


@router.post("/import-save", response_model=ImportSaveResponse)
async def post_import_save(file: UploadFile = File(...)) -> ImportSaveResponse:
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".eu4") as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            s = sessions.load(Path(tmp.name), file.filename or "upload")
        except ironman_melt.MeltUnavailableError as e:
            raise HTTPException(422, str(e)) from e
        except zipfile.BadZipFile as e:
            raise HTTPException(422, f"Not a valid .eu4 save file: {e}") from e
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
    graph = load_trade_graph()
    inputs, tag = s.world.inputs, s.player
    current = _current_placement(s)
    warnings: list[str] = []
    if inputs.game_version != calc.SUPPORTED_GAME_VERSION:
        warnings.append(f"The save is from game version {inputs.game_version}; the calculation was verified on {calc.SUPPORTED_GAME_VERSION}.")
    unknown = sorted({n for n in inputs.nodes if n not in graph})
    if unknown:
        warnings.append(f"The save has trade nodes this game version's map does not know (ignored): {', '.join(unknown)}.")
    if tag not in s.observed.trade_efficiency:
        warnings.append("Your trade efficiency could not be read from the save (you collect nowhere); set it by hand.")
    presence = {node for (node, t), e in inputs.entries.items()
                if t == tag and node in graph and (e.province_power > 0 or e.ship_power > 0 or e.has_capital or e.has_trader)}
    unit = calc.ship_unit_power(inputs, s.observed).get(tag)
    return ImportSaveResponse(
        save_id=s.save_id, player_tag=tag, date=inputs.date, calc_version=calc.CALC_VERSION, warnings=warnings,
        current_allocation={n: NodeAllocationIn.from_decision(d) for n, d in current.items() if n in graph},
        suggested_home_node=_home_node(s),
        suggested_trade_efficiency=s.observed.trade_efficiency.get(tag),
        actual_current_income=sum(r.money or 0.0 for (_n, t), r in s.world.recorded.entries.items() if t == tag),
        suggested_max_merchants=max(inputs.player_merchants, sum(1 for d in current.values() if d.action != Action.NONE)),
        suggested_max_light_ships=max(inputs.player_light_ships, sum(d.light_ships for d in current.values())),
        suggested_power_per_light_ship=unit,
        suggested_candidate_nodes=sorted(presence | set(current)),
    )


@router.post("/simulate", response_model=SimulateResponse)
def post_simulate(req: SimulateRequest) -> SimulateResponse:
    graph, s = load_trade_graph(), _session(req.save_id)
    placement = _placement(req.allocation, graph)
    return _simulation(s, graph, _evaluate(s, req, placement), placement)


@router.post("/node-options", response_model=NodeOptionsResponse)
def post_node_options(req: NodeOptionsRequest) -> NodeOptionsResponse:
    graph, s = load_trade_graph(), _session(req.save_id)
    if req.node_id not in graph:
        raise HTTPException(422, f"Unknown trade node id: {req.node_id}")
    base = _placement(req.allocation, graph)
    cur = base.get(req.node_id, NodeDecision())

    def run(d: NodeDecision) -> tuple[dict[str, NodeDecision], TradeResult]:
        p = dict(base)
        p[req.node_id] = d
        return p, _evaluate(s, req, p)

    current_income = _evaluate(s, req, base).income(s.player)
    options = []
    for action, target in [(Action.NONE, None), (Action.COLLECT, None), *[(Action.STEER, t) for t in graph.outgoing(req.node_id)]]:
        p, r = run(NodeDecision(action, target, cur.light_ships))
        income = r.income(s.player)
        options.append(MerchantOptionOut(
            action=action, steer_target=target, steer_target_display_name=graph.display_name(target) if target else None,
            total_income=income, formula_total_income=income,
            is_current=(action == cur.action and target == (cur.steer_target if cur.action == Action.STEER else None)),
            node=_breakdown(s, graph, r, p, req.node_id),
        ))
    curve: list[ShipPointOut] = []
    if not graph.is_inland(req.node_id):
        top = min(max(req.max_light_ships, cur.light_ships, 20), SHIP_CURVE_MAX)
        for n in range(top + 1):
            p, r = run(NodeDecision(cur.action, cur.steer_target, n))
            b = _breakdown(s, graph, r, p, req.node_id)
            curve.append(ShipPointOut(ships=n, total_income=r.income(s.player), formula_total_income=r.income(s.player),
                                      player_power=b.player_power, player_share=b.player_share, node_income=b.player_income))
    return NodeOptionsResponse(node_id=req.node_id, display_name=graph.display_name(req.node_id),
                               current_total_income=current_income, formula_current_total_income=current_income,
                               merchant_options=options, ship_curve=curve)


def _marginal(m: Marginal, graph: TradeGraph) -> MarginalValueOut:
    return MarginalValueOut(
        label=m.label, income=m.income, delta_vs_optimal=m.delta_vs_optimal, node_id=m.node_id,
        node_display_name=graph.display_name(m.node_id) if m.node_id else None, change=m.change,
        merchant_action=m.action, steer_target=m.steer_target,
        steer_target_display_name=graph.display_name(m.steer_target) if m.steer_target else None,
    )


@router.post("/optimize", response_model=OptimizeResponse)
def post_optimize(req: OptimizeRequest) -> OptimizeResponse:
    graph, s = load_trade_graph(), _session(req.save_id)
    if req.home_node not in graph:
        raise HTTPException(422, f"Unknown home node id: {req.home_node}")
    candidates = req.candidate_nodes if req.candidate_nodes is not None else sorted({n for (n, t) in s.world.inputs.entries if t == s.player})
    unknown = [n for n in candidates if n not in graph]
    if unknown:
        raise HTTPException(422, f"Unknown trade node id(s): {unknown}")
    current = _placement(req.current_allocation, graph) if req.current_allocation is not None else None
    within_budget = current is not None and sum(1 for d in current.values() if d.action != Action.NONE) <= req.max_merchants \
        and sum(d.light_ships for d in current.values()) <= req.max_light_ships
    config = OptimizeConfig(home_node=req.home_node, candidate_nodes=candidates, max_merchants=req.max_merchants,
                            max_light_ships=req.max_light_ships, random_seed=req.random_seed, max_restarts=req.max_restarts,
                            starts=[current] if within_budget else [])
    what_if = s.what_if(req.params.trade_efficiency, req.params.power_per_light_ship)
    try:
        result = optimize(what_if, graph, config)
    except UnknownVariable as e:
        raise HTTPException(422, f"The calculation needs a value this save does not give: {e}") from e
    current_income = _evaluate(s, req, current).income(s.player) if current is not None else None
    actions = [
        RecommendedAction(node_id=n, display_name=graph.display_name(n), merchant_action=d.action, steer_target=d.steer_target,
                          steer_target_display_name=graph.display_name(d.steer_target) if d.steer_target else None,
                          light_ships=d.light_ships)
        for n, d in sorted(result.placement.items())
    ]
    breakdown = _simulation(s, graph, _evaluate(s, req, result.placement), result.placement)
    return OptimizeResponse(
        income=result.income, baseline_income=result.baseline_income, current_income=current_income,
        income_gain_vs_current=(result.income - current_income) if current_income is not None else None,
        recommended_actions=actions,
        merchant_marginals=[_marginal(m, graph) for m in result.merchant_marginals],
        ship_marginals=[_marginal(m, graph) for m in result.ship_marginals],
        breakdown=breakdown,
    )

