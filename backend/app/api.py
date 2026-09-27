"""API routes: trade node graph, save import, simulate, optimize."""
from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.engine.optimize import optimize as run_optimize
from app.engine.simulate import simulate as run_simulate
from app.parsing import rakaly, save as save_parsing
from app.parsing.tradenodes import load_trade_graph
from app.schemas import (
    ImportSaveResponse,
    NodeAllocationIn,
    NodeStateIn,
    OptimizeRequest,
    OptimizeResponse,
    SimulateRequest,
    SimulateResponse,
    TradeGraphOut,
    TradeNodeOut,
)

router = APIRouter(prefix="/api")


@router.get("/tradenodes", response_model=TradeGraphOut)
def get_tradenodes() -> TradeGraphOut:
    graph = load_trade_graph()
    return TradeGraphOut(
        game_version=graph.game_version,
        end_nodes=graph.end_nodes,
        nodes=[
            TradeNodeOut(
                node_id=info.node_id,
                display_name=info.display_name,
                inland=info.inland,
                outgoing=list(info.outgoing),
            )
            for info in graph.nodes.values()
        ],
    )


@router.post("/simulate", response_model=SimulateResponse)
def post_simulate(req: SimulateRequest) -> SimulateResponse:
    graph = load_trade_graph()
    node_states = {nid: s.to_engine() for nid, s in req.node_states.items()}
    from app.engine.model import Allocation

    allocation = Allocation(nodes={nid: a.to_engine() for nid, a in req.allocation.items()})
    result = run_simulate(graph, node_states, allocation, req.params.to_engine())
    display_names = {nid: graph.display_name(nid) for nid in node_states if nid in graph}
    return SimulateResponse.from_engine(result, display_names)


@router.post("/optimize", response_model=OptimizeResponse)
def post_optimize(req: OptimizeRequest) -> OptimizeResponse:
    graph = load_trade_graph()
    unknown = [nid for nid in req.node_states if nid not in graph]
    if unknown:
        raise HTTPException(422, f"Unknown trade node id(s): {unknown}")
    if req.home_node not in graph:
        raise HTTPException(422, f"Unknown home node id: {req.home_node}")

    node_states = {nid: s.to_engine() for nid, s in req.node_states.items()}
    params = req.params.to_engine()
    config = req.to_engine_config()

    result = run_optimize(graph, node_states, params, config)

    from app.engine.model import Allocation

    current_income = None
    if req.current_allocation is not None:
        current_alloc = Allocation(nodes={nid: a.to_engine() for nid, a in req.current_allocation.items()})
        current_income = run_simulate(graph, node_states, current_alloc, params).total_income

    breakdown = run_simulate(graph, node_states, result.allocation, params)
    display_names = {nid: graph.display_name(nid) for nid in graph.nodes}
    return OptimizeResponse.from_engine(result, display_names, breakdown, current_income)


@router.post("/import-save", response_model=ImportSaveResponse)
async def post_import_save(file: UploadFile = File(...)) -> ImportSaveResponse:
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".eu4") as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            parsed = save_parsing.load_save(Path(tmp.name))
        except rakaly.MeltUnavailableError as e:
            # Ironman save, and neither the pdx.tools automation nor a
            # local rakaly CLI could melt it -- message already tells the
            # user exactly what to do (start the melt worker, or melt via
            # pdx.tools by hand and re-upload, or enter data manually).
            raise HTTPException(422, str(e)) from e
        except rakaly.RakalyNotFound as e:
            raise HTTPException(422, str(e)) from e
        except rakaly.RakalyMeltError as e:
            raise HTTPException(422, f"Failed to melt save: {e}") from e
        except zipfile.BadZipFile as e:
            raise HTTPException(422, f"Not a valid .eu4 save file: {e}") from e
        except ValueError as e:
            raise HTTPException(422, str(e)) from e

    graph = load_trade_graph()
    node_states, current_allocation, home_node = save_parsing.build_node_states_from_save(parsed, graph)

    warnings = list(parsed.warnings)
    known_states = {}
    for nid, state in node_states.items():
        if nid not in graph:
            warnings.append(f"Save referenced unknown trade node '{nid}' (skipped).")
            continue
        known_states[nid] = state

    return ImportSaveResponse(
        player_tag=parsed.player_tag,
        warnings=warnings,
        node_states={nid: NodeStateIn(**s.__dict__) for nid, s in known_states.items()},
        current_allocation={
            nid: NodeAllocationIn(
                merchant_action=a.merchant_action,
                steer_target=a.steer_target,
                light_ships=a.light_ships,
            )
            for nid, a in current_allocation.items()
            if nid in known_states
        },
        suggested_home_node=home_node,
        suggested_trade_efficiency=parsed.suggested_trade_efficiency,
        actual_current_income=parsed.actual_current_income,
    )
