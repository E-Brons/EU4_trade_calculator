import pytest

from app.engine.model import NodeState, Params
from app.engine.optimize import OptimizeConfig, optimize, _exhaustive_search, _heuristic_search
from app.engine.simulate import simulate
from app.parsing.tradenodes import TradeGraph


def make_graph(edges: dict[str, list[str]], inland: set[str] = frozenset()) -> TradeGraph:
    raw = {
        "game_version": "test",
        "end_nodes": [n for n, outs in edges.items() if not outs],
        "nodes": {
            n: {
                "display_name": n,
                "inland": n in inland,
                "outgoing": [{"target": t} for t in outs],
            }
            for n, outs in edges.items()
        },
    }
    return TradeGraph(raw)


def test_optimizer_puts_only_merchant_at_home_when_thats_optimal():
    # A single isolated home node with a rival: the only lever is putting a
    # merchant there, which the optimizer should discover trivially.
    graph = make_graph({"home": []})
    states = {"home": NodeState(node_id="home", local_value=100.0, is_home=True, player_base_power=5.0, other_collect_power=15.0)}
    params = Params(merchant_power=5.0)
    config = OptimizeConfig(home_node="home", candidate_nodes=["home"], max_merchants=1, max_light_ships=0)

    result = optimize(graph, states, params, config)
    assert result.allocation.get("home").merchant_action.value in ("collect", "none")
    # With a merchant (power 5+5=10 vs baseline 5) income should exceed baseline.
    assert result.income > result.baseline_income


def test_optimizer_matches_exhaustive_search_on_small_network():
    graph = make_graph({
        "far": ["mid"],
        "mid": ["home", "rival_sink"],
        "home": [],
        "rival_sink": [],
    })
    states = {
        "far": NodeState(node_id="far", local_value=50.0, player_base_power=8.0),
        "mid": NodeState(node_id="mid", local_value=30.0, player_base_power=6.0, other_steer_power={"rival_sink": 4.0}),
        "home": NodeState(node_id="home", is_home=True, player_base_power=3.0),
        "rival_sink": NodeState(node_id="rival_sink", other_collect_power=10.0),
    }
    params = Params(merchant_power=6.0, power_per_light_ship=2.0)
    candidates = ["far", "mid", "home"]
    config = OptimizeConfig(home_node="home", candidate_nodes=candidates, max_merchants=2, max_light_ships=0)

    exhaustive_alloc = _exhaustive_search(graph, states, params, config, candidates)
    exhaustive_income = simulate(graph, states, exhaustive_alloc, params).total_income

    heuristic_alloc = _heuristic_search(graph, states, params, config, candidates)
    heuristic_income = simulate(graph, states, heuristic_alloc, params).total_income

    assert heuristic_income == pytest.approx(exhaustive_income, rel=1e-6)


def test_optimizer_never_exceeds_merchant_budget():
    graph = make_graph({"a": ["home"], "b": ["home"], "home": []})
    states = {
        "a": NodeState(node_id="a", local_value=40.0, player_base_power=5.0),
        "b": NodeState(node_id="b", local_value=40.0, player_base_power=5.0),
        "home": NodeState(node_id="home", is_home=True, player_base_power=5.0),
    }
    params = Params(merchant_power=4.0)
    config = OptimizeConfig(home_node="home", candidate_nodes=["a", "b", "home"], max_merchants=1, max_light_ships=0)
    result = optimize(graph, states, params, config)
    assert result.allocation.merchant_count() <= 1


def test_optimizer_respects_merchant_budget_on_larger_random_network():
    # Regression test: a random-restart perturbation could previously
    # assign more merchants than the budget allows, and local search never
    # forced a repair back down (see _complete_and_refine's repair step).
    import random

    rng = random.Random(7)
    home = "home"
    others = [f"n{i}" for i in range(14)]
    edges = {home: []}
    for n in others:
        edges[n] = [home]
    graph = make_graph(edges)
    states = {home: NodeState(node_id=home, is_home=True, player_base_power=5.0)}
    for n in others:
        states[n] = NodeState(
            node_id=n,
            local_value=rng.uniform(5, 80),
            player_base_power=rng.uniform(2, 20),
            other_collect_power=rng.uniform(0, 40),
        )
    params = Params(merchant_power=6.0, power_per_light_ship=1.5)
    config = OptimizeConfig(
        home_node=home, candidate_nodes=others + [home], max_merchants=5, max_light_ships=30, random_seed=1
    )
    result = optimize(graph, states, params, config)
    assert result.allocation.merchant_count() <= 5
    assert result.allocation.light_ship_count() <= 30


def test_optimizer_respects_ship_budget_and_inland_nodes_get_no_ships():
    graph = make_graph({"home": []}, inland={"home"})
    states = {"home": NodeState(node_id="home", is_home=True, local_value=100.0, player_base_power=5.0)}
    params = Params(power_per_light_ship=10.0, ship_chunk=5)
    config = OptimizeConfig(home_node="home", candidate_nodes=["home"], max_merchants=0, max_light_ships=20)
    result = optimize(graph, states, params, config)
    assert result.allocation.get("home").light_ships == 0  # inland: ships shouldn't help
    assert result.allocation.light_ship_count() <= 20


def test_marginal_value_of_extra_merchant_is_reported():
    graph = make_graph({"far": ["home"], "home": []})
    states = {
        "far": NodeState(node_id="far", local_value=100.0, player_base_power=5.0),
        "home": NodeState(node_id="home", is_home=True, player_base_power=5.0),
    }
    params = Params(merchant_power=10.0)
    config = OptimizeConfig(home_node="home", candidate_nodes=["far", "home"], max_merchants=1, max_light_ships=0)
    result = optimize(graph, states, params, config)
    assert len(result.merchant_marginals) == 2
    more = next(m for m in result.merchant_marginals if "more" in m.label)
    assert more.income >= result.income  # a 2nd merchant should never make things worse
