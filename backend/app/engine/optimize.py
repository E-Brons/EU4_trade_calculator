"""Discrete search for the merchant/ship allocation that maximizes the
player's total trade income.

Decision variables per candidate node: a merchant action (None / Collect /
Steer-to-X) and a number of light ships (in chunks). With up to ~15-20
candidate nodes and a handful of merchants this is too large to brute
force in general, so we use the approach agreed with the user:

  1. Seed with the "obvious" allocation (collect at home, steer the nodes
     on the path to home, ships to the best marginal spot).
  2. Fill any remaining merchants one at a time, trying each option and
     keeping the best (marginal completion).
  3. Local search (1-opt moves + a few random restarts) until no single
     change improves income.
  4. If the search space is small enough, brute force it instead and use
     that as the answer (also used by tests to validate the heuristic).
"""
from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

from app.engine.model import Allocation, MerchantAction, NodeAllocation, NodeState, Params
from app.engine.simulate import simulate
from app.parsing.tradenodes import TradeGraph

EXHAUSTIVE_LIMIT = 200_000


@dataclass
class OptimizeConfig:
    home_node: str
    candidate_nodes: list[str]          # nodes the optimizer is allowed to touch
    max_merchants: int
    max_light_ships: int
    random_seed: int = 0
    max_restarts: int = 3


@dataclass
class MarginalValue:
    """Value of adding/removing one merchant or chunk of ships, relative to the
    optimal allocation, and exactly where the change would be made.

    `node_id` is where the merchant/ships would be added (change="add") or
    taken from (change="remove"); None when there is no beneficial place to add
    one (or nothing to remove). For merchants, `merchant_action`/`steer_target`
    is the action to start (add) or the action being given up (remove)."""

    label: str
    income: float
    delta_vs_optimal: float
    node_id: str | None = None
    change: str | None = None  # "add" | "remove"
    merchant_action: MerchantAction | None = None
    steer_target: str | None = None


@dataclass
class OptimizeResult:
    allocation: Allocation
    income: float
    baseline_income: float          # income with no player action anywhere (nodes just passive/home)
    current_income: float | None    # income under the allocation taken from the save, if provided
    merchant_marginals: list[MarginalValue]
    ship_marginals: list[MarginalValue]


def _node_options(graph: TradeGraph, node_id: str, home_node: str) -> list[NodeAllocation]:
    """All merchant actions worth considering at a node (ignoring ships,
    which are optimized as a separate, mostly-independent dimension).

    Collect is offered even at the home node: the player always collects
    there regardless, but stationing a merchant there (Collect) adds
    merchant trade power and the home-node merchant bonus, so it's a
    distinct, often-optimal option from doing nothing."""
    options = [
        NodeAllocation(merchant_action=MerchantAction.NONE),
        NodeAllocation(merchant_action=MerchantAction.COLLECT),
    ]
    for target in graph.outgoing(node_id):
        options.append(NodeAllocation(merchant_action=MerchantAction.STEER, steer_target=target))
    return options


def _score(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    allocation: Allocation,
    params: Params,
) -> float:
    return simulate(graph, node_states, allocation, params).total_income


def optimize(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
) -> OptimizeResult:
    candidates = [n for n in config.candidate_nodes if n in graph.nodes]
    if config.home_node not in candidates:
        candidates = [config.home_node] + candidates

    baseline_income = _score(graph, node_states, Allocation(), params)

    search_space_size = _estimate_search_space(graph, candidates, config, params)
    if search_space_size <= EXHAUSTIVE_LIMIT:
        best_alloc = _exhaustive_search(graph, node_states, params, config, candidates)
    else:
        best_alloc = _heuristic_search(graph, node_states, params, config, candidates)

    best_income = _score(graph, node_states, best_alloc, params)

    merchant_marginals = _merchant_marginals(graph, node_states, params, config, candidates, best_alloc, best_income)
    ship_marginals = _ship_marginals(graph, node_states, params, config, candidates, best_alloc, best_income)

    return OptimizeResult(
        allocation=best_alloc,
        income=best_income,
        baseline_income=baseline_income,
        current_income=None,
        merchant_marginals=merchant_marginals,
        ship_marginals=ship_marginals,
    )


def _estimate_search_space(graph: TradeGraph, candidates: list[str], config: OptimizeConfig, params: Params) -> int:
    merchant_options_per_node = [len(_node_options(graph, n, config.home_node)) for n in candidates]
    # Rough upper bound: product of per-node option counts, capped, times
    # the ship placements. Good enough to decide exhaustive vs heuristic.
    total = 1
    for opts in merchant_options_per_node:
        total *= opts
        if total > EXHAUSTIVE_LIMIT:
            return total
    ship_slots = config.max_light_ships // max(params.ship_chunk, 1) + 1
    total *= max(ship_slots, 1) ** min(len(candidates), 3)
    return total


def _exhaustive_search(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
    candidates: list[str],
) -> Allocation:
    best_alloc: Allocation | None = None
    best_income = float("-inf")

    per_node_options = {n: _node_options(graph, n, config.home_node) for n in candidates}
    ship_chunk = params.ship_chunk
    ship_amounts = list(range(0, config.max_light_ships + 1, ship_chunk))
    sea_candidates = [n for n in candidates if not graph.is_inland(n)]

    for combo in itertools.product(*(per_node_options[n] for n in candidates)):
        n_merchants = sum(1 for a in combo if a.merchant_action != MerchantAction.NONE)
        if n_merchants > config.max_merchants:
            continue
        alloc = Allocation()
        for node_id, a in zip(candidates, combo):
            alloc.nodes[node_id] = NodeAllocation(a.merchant_action, a.steer_target, 0)

        best_ship_income, best_ship_alloc = _best_ship_allocation(
            graph, node_states, params, alloc, sea_candidates, ship_amounts, config.max_light_ships
        )
        if best_ship_income > best_income:
            best_income = best_ship_income
            best_alloc = best_ship_alloc

    return best_alloc if best_alloc is not None else Allocation()


def _best_ship_allocation(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    base_alloc: Allocation,
    sea_candidates: list[str],
    ship_amounts: list[int],
    max_ships: int,
) -> tuple[float, Allocation]:
    """Greedily (and, for small cases, exhaustively) place ships given a
    fixed merchant allocation."""
    if not sea_candidates:
        return _score(graph, node_states, base_alloc, params), base_alloc

    if len(sea_candidates) ** len(ship_amounts) <= 5000 and len(sea_candidates) <= 4:
        best_income = float("-inf")
        best_alloc = base_alloc
        for combo in itertools.product(ship_amounts, repeat=len(sea_candidates)):
            if sum(combo) > max_ships:
                continue
            alloc = base_alloc.copy()
            for node_id, ships in zip(sea_candidates, combo):
                a = alloc.get(node_id)
                a.light_ships = ships
            income = _score(graph, node_states, alloc, params)
            if income > best_income:
                best_income = income
                best_alloc = alloc
        return best_income, best_alloc

    return _greedy_ship_allocation(graph, node_states, params, base_alloc, sea_candidates, max_ships)


def _greedy_ship_allocation(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    base_alloc: Allocation,
    sea_candidates: list[str],
    max_ships: int,
) -> tuple[float, Allocation]:
    alloc = base_alloc.copy()
    remaining = max_ships
    chunk = params.ship_chunk
    current_income = _score(graph, node_states, alloc, params)
    while remaining >= chunk:
        best_gain = 0.0
        best_node = None
        for node_id in sea_candidates:
            trial = alloc.copy()
            trial.get(node_id).light_ships += chunk
            income = _score(graph, node_states, trial, params)
            gain = income - current_income
            if gain > best_gain:
                best_gain = gain
                best_node = node_id
        if best_node is None:
            break
        alloc.get(best_node).light_ships += chunk
        current_income += best_gain
        remaining -= chunk
    return current_income, alloc


def _seed_allocation(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
    candidates: list[str],
) -> Allocation:
    alloc = Allocation()
    merchants_left = config.max_merchants

    # Home node always collects; give it a merchant first if any are
    # available, for the home-node merchant bonus.
    if merchants_left > 0:
        alloc.get(config.home_node).merchant_action = MerchantAction.COLLECT
        merchants_left -= 1

    # Steer every other candidate toward home along its shortest known path.
    for node_id in candidates:
        if node_id == config.home_node or merchants_left <= 0:
            continue
        path = graph.upstream_path_to(node_id, config.home_node)
        if path and len(path) >= 2:
            alloc.get(node_id).merchant_action = MerchantAction.STEER
            alloc.get(node_id).steer_target = path[1]
            merchants_left -= 1

    # Ships: greedy placement with whatever merchant layout we have so far.
    sea_candidates = [n for n in candidates if not graph.is_inland(n)]
    _, alloc = _greedy_ship_allocation(graph, node_states, params, alloc, sea_candidates, config.max_light_ships)
    return alloc


def _heuristic_search(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
    candidates: list[str],
) -> Allocation:
    rng = random.Random(config.random_seed)
    best_overall: Allocation | None = None
    best_overall_income = float("-inf")

    for restart in range(config.max_restarts + 1):
        if restart == 0:
            alloc = _seed_allocation(graph, node_states, params, config, candidates)
        else:
            alloc = _perturb(_seed_allocation(graph, node_states, params, config, candidates), graph, candidates, config, rng)

        alloc = _complete_and_refine(graph, node_states, params, config, candidates, alloc)
        income = _score(graph, node_states, alloc, params)
        if income > best_overall_income:
            best_overall_income = income
            best_overall = alloc

    return best_overall if best_overall is not None else Allocation()


def _complete_and_refine(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
    candidates: list[str],
    alloc: Allocation,
) -> Allocation:
    per_node_options = {n: _node_options(graph, n, config.home_node) for n in candidates}
    sea_candidates = [n for n in candidates if not graph.is_inland(n)]

    def used_merchants(a: Allocation) -> int:
        return sum(1 for n in candidates if a.get(n).merchant_action != MerchantAction.NONE)

    # Repair: a perturbed seed (from a random restart) may have more
    # merchants placed than the budget allows. Drop merchants one at a
    # time -- each time removing whichever costs the least income -- until
    # back within budget, before doing anything else.
    while used_merchants(alloc) > config.max_merchants:
        best_loss, best_node = float("inf"), None
        base_income = _score(graph, node_states, alloc, params)
        for node_id in candidates:
            if alloc.get(node_id).merchant_action == MerchantAction.NONE:
                continue
            trial = alloc.copy()
            trial.get(node_id).merchant_action = MerchantAction.NONE
            trial.get(node_id).steer_target = None
            loss = base_income - _score(graph, node_states, trial, params)
            if loss < best_loss:
                best_loss, best_node = loss, node_id
        alloc.get(best_node).merchant_action = MerchantAction.NONE
        alloc.get(best_node).steer_target = None

    # Marginal completion: add merchants one at a time to whichever free
    # node/option gives the best gain, until max_merchants is used or no
    # option helps.
    improved = True
    while used_merchants(alloc) < config.max_merchants and improved:
        improved = False
        current_income = _score(graph, node_states, alloc, params)
        best_gain, best_node, best_option = 0.0, None, None
        for node_id in candidates:
            if alloc.get(node_id).merchant_action != MerchantAction.NONE:
                continue
            for option in per_node_options[node_id]:
                if option.merchant_action == MerchantAction.NONE:
                    continue
                trial = alloc.copy()
                trial.nodes[node_id] = NodeAllocation(option.merchant_action, option.steer_target, alloc.get(node_id).light_ships)
                income = _score(graph, node_states, trial, params)
                gain = income - current_income
                if gain > best_gain:
                    best_gain, best_node, best_option = gain, node_id, option
        if best_node is not None:
            alloc.nodes[best_node] = NodeAllocation(best_option.merchant_action, best_option.steer_target, alloc.get(best_node).light_ships)
            improved = True

    # Local search: 1-opt over merchant placement/action, then re-place ships.
    changed = True
    while changed:
        changed = False
        current_income = _score(graph, node_states, alloc, params)

        for node_id in candidates:
            current_action = alloc.get(node_id)
            best_local_income = current_income
            best_local_option = current_action
            for option in per_node_options[node_id]:
                if used_merchants(alloc) - (1 if current_action.merchant_action != MerchantAction.NONE else 0) \
                        + (1 if option.merchant_action != MerchantAction.NONE else 0) > config.max_merchants:
                    continue
                trial = alloc.copy()
                trial.nodes[node_id] = NodeAllocation(option.merchant_action, option.steer_target, current_action.light_ships)
                income = _score(graph, node_states, trial, params)
                if income > best_local_income:
                    best_local_income = income
                    best_local_option = option
            if best_local_option is not current_action:
                alloc.nodes[node_id] = NodeAllocation(best_local_option.merchant_action, best_local_option.steer_target, current_action.light_ships)
                current_income = best_local_income
                changed = True

        ship_income, alloc = _greedy_ship_allocation(graph, node_states, params, _zero_ships(alloc), sea_candidates, config.max_light_ships)
        if ship_income > current_income + 1e-9:
            changed = True

    return alloc


def _zero_ships(alloc: Allocation) -> Allocation:
    a = alloc.copy()
    for na in a.nodes.values():
        na.light_ships = 0
    return a


def _perturb(alloc: Allocation, graph: TradeGraph, candidates: list[str], config: OptimizeConfig, rng: random.Random) -> Allocation:
    """Randomly reassign a couple of nodes' merchant actions, to give local
    search a different starting point on each restart."""
    alloc = alloc.copy()
    for _ in range(min(2, len(candidates))):
        node_id = rng.choice(candidates)
        options = _node_options(graph, node_id, config.home_node)
        opt = rng.choice(options)
        alloc.nodes[node_id] = NodeAllocation(opt.merchant_action, opt.steer_target, alloc.get(node_id).light_ships)
    return alloc


def _merchant_marginals(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
    candidates: list[str],
    best_alloc: Allocation,
    best_income: float,
) -> list[MarginalValue]:
    """One fewer / one more merchant, each applied to the optimal allocation:
    the removal that loses least, and the best spot for a new merchant."""

    def has_merchant(node_id: str) -> bool:
        a = best_alloc.nodes.get(node_id)
        return a is not None and a.merchant_action != MerchantAction.NONE

    def with_action(node_id: str, action: MerchantAction, target: str | None) -> Allocation:
        trial = best_alloc.copy()
        ships = trial.get(node_id).light_ships
        trial.nodes[node_id] = NodeAllocation(action, target, ships)
        return trial

    # --- one fewer: take a merchant off the node where it is worth least.
    fewer = MarginalValue(label="one fewer merchant", income=best_income, delta_vs_optimal=0.0)
    best_removal: tuple[float, str] | None = None
    for node_id in candidates:
        if not has_merchant(node_id):
            continue
        income = _score(graph, node_states, with_action(node_id, MerchantAction.NONE, None), params)
        if best_removal is None or income > best_removal[0]:
            best_removal = (income, node_id)
    if best_removal is not None:
        income, node_id = best_removal
        old = best_alloc.nodes[node_id]
        fewer = MarginalValue(
            label="one fewer merchant",
            income=income,
            delta_vs_optimal=income - best_income,
            node_id=node_id,
            change="remove",
            merchant_action=old.merchant_action,
            steer_target=old.steer_target,
        )

    # --- one more: put a new merchant where it adds most (only counts nodes
    # that have no merchant yet; changing an existing one doesn't use a new one).
    more = MarginalValue(label="one more merchant", income=best_income, delta_vs_optimal=0.0)
    best_add: tuple[float, str, NodeAllocation] | None = None
    for node_id in candidates:
        if has_merchant(node_id):
            continue
        for opt in _node_options(graph, node_id, config.home_node):
            if opt.merchant_action == MerchantAction.NONE:
                continue
            income = _score(graph, node_states, with_action(node_id, opt.merchant_action, opt.steer_target), params)
            if best_add is None or income > best_add[0]:
                best_add = (income, node_id, opt)
    if best_add is not None and best_add[0] > best_income + 1e-9:
        income, node_id, opt = best_add
        more = MarginalValue(
            label="one more merchant",
            income=income,
            delta_vs_optimal=income - best_income,
            node_id=node_id,
            change="add",
            merchant_action=opt.merchant_action,
            steer_target=opt.steer_target,
        )
    return [fewer, more]


def _ship_marginals(
    graph: TradeGraph,
    node_states: dict[str, NodeState],
    params: Params,
    config: OptimizeConfig,
    candidates: list[str],
    best_alloc: Allocation,
    best_income: float,
) -> list[MarginalValue]:
    """`chunk` fewer / more light ships, each applied to the optimal allocation:
    the node where taking ships hurts least, and the node where adding helps most."""
    chunk = params.ship_chunk
    fewer_label = f"{chunk} fewer light ships"
    more_label = f"{chunk} more light ships"

    fewer = MarginalValue(label=fewer_label, income=best_income, delta_vs_optimal=0.0)
    best_removal: tuple[float, str] | None = None
    for node_id, a in best_alloc.nodes.items():
        if a.light_ships < chunk:
            continue
        trial = best_alloc.copy()
        trial.get(node_id).light_ships -= chunk
        income = _score(graph, node_states, trial, params)
        if best_removal is None or income > best_removal[0]:
            best_removal = (income, node_id)
    if best_removal is not None:
        income, node_id = best_removal
        fewer = MarginalValue(
            label=fewer_label, income=income, delta_vs_optimal=income - best_income, node_id=node_id, change="remove"
        )

    more = MarginalValue(label=more_label, income=best_income, delta_vs_optimal=0.0)
    best_add: tuple[float, str] | None = None
    for node_id in candidates:
        if graph.is_inland(node_id):
            continue
        trial = best_alloc.copy()
        trial.get(node_id).light_ships += chunk
        income = _score(graph, node_states, trial, params)
        if best_add is None or income > best_add[0]:
            best_add = (income, node_id)
    if best_add is not None and best_add[0] > best_income + 1e-9:
        income, node_id = best_add
        more = MarginalValue(
            label=more_label, income=income, delta_vs_optimal=income - best_income, node_id=node_id, change="add"
        )
    return [fewer, more]
