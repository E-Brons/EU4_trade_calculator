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


def test_local_search_terminates_with_fine_ship_chunk_and_many_sea_candidates():
    # Regression test: with ship_chunk=1 (the default), the 1-opt local
    # search in _complete_and_refine can discover a single ship worth
    # moving by a sliver every round, which can flip a near-tied merchant
    # choice, which re-ties the ships -- a genuine oscillation between
    # merchant 1-opt and ship re-placement that a coarser chunk mostly
    # hides. Confirmed against a real save: this hung for 15+ minutes
    # (>900s, never completing) before MAX_LOCAL_SEARCH_ROUNDS was added.
    # Many sea candidates + many ships + chunk=1 reproduces the same
    # shape here; the real assertion is just that this returns at all,
    # and promptly -- not oscillates forever.
    import random
    import time

    rng = random.Random(3)
    home = "home"
    others = [f"n{i}" for i in range(12)]
    edges = {home: []}
    for n in others:
        edges[n] = [home]
    graph = make_graph(edges)  # none inland -- every node is a sea candidate
    states = {home: NodeState(node_id=home, is_home=True, player_base_power=5.0)}
    for n in others:
        states[n] = NodeState(
            node_id=n,
            local_value=rng.uniform(20, 30),  # narrow range: encourages near-ties
            player_base_power=rng.uniform(2, 6),
            other_collect_power=rng.uniform(15, 25),
        )
    params = Params(merchant_power=6.0, power_per_light_ship=1.5, ship_chunk=1)
    config = OptimizeConfig(
        home_node=home, candidate_nodes=others + [home], max_merchants=6, max_light_ships=80, random_seed=2
    )

    start = time.monotonic()
    result = optimize(graph, states, params, config)
    elapsed = time.monotonic() - start

    assert elapsed < 15.0, f"optimize() took {elapsed:.1f}s -- local search likely regressed to unbounded oscillation"
    assert result.allocation.merchant_count() <= 6
    assert result.allocation.light_ship_count() <= 80


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


def _two_node_case(max_merchants=1, max_ships=0, ship_power=3.0):
    graph = make_graph({"far": ["home"], "home": []})
    states = {
        "far": NodeState(node_id="far", local_value=100.0, player_base_power=5.0, other_collect_power=5.0),
        "home": NodeState(node_id="home", is_home=True, local_value=60.0, player_base_power=5.0, other_collect_power=5.0),
    }
    params = Params(merchant_power=10.0, power_per_light_ship=ship_power)
    config = OptimizeConfig(
        home_node="home",
        candidate_nodes=["far", "home"],
        max_merchants=max_merchants,
        max_light_ships=max_ships,
    )
    return graph, states, params, config


def test_merchant_marginals_name_the_node_to_take_from_and_add_to():
    graph, states, params, config = _two_node_case(max_merchants=1)
    result = optimize(graph, states, params, config)
    placed = [n for n, a in result.allocation.nodes.items() if a.merchant_action.value != "none"]
    assert len(placed) == 1
    fewer = next(m for m in result.merchant_marginals if "fewer" in m.label)
    more = next(m for m in result.merchant_marginals if "more" in m.label)

    # Removing the only merchant: it must come from where it is, and costs income.
    assert fewer.change == "remove"
    assert fewer.node_id == placed[0]
    assert fewer.merchant_action == result.allocation.nodes[placed[0]].merchant_action
    assert fewer.delta_vs_optimal <= 0

    # Adding one: goes to the other node (the one without a merchant), and helps.
    assert more.change == "add"
    assert more.node_id is not None and more.node_id != placed[0]
    assert more.merchant_action is not None and more.merchant_action.value != "none"
    assert more.delta_vs_optimal > 0
    assert more.income == pytest.approx(result.income + more.delta_vs_optimal)


def test_merchant_marginals_have_no_location_when_nothing_to_remove_or_add():
    graph, states, params, config = _two_node_case(max_merchants=0)
    result = optimize(graph, states, params, config)
    fewer = next(m for m in result.merchant_marginals if "fewer" in m.label)
    assert fewer.node_id is None and fewer.change is None and fewer.delta_vs_optimal == 0


def test_ship_marginals_name_the_node_to_take_from_and_add_to():
    graph, states, params, config = _two_node_case(max_merchants=0, max_ships=2, ship_power=4.0)
    result = optimize(graph, states, params, config)
    ships_at = {n: a.light_ships for n, a in result.allocation.nodes.items() if a.light_ships}
    assert ships_at, "optimizer should use ships here"
    fewer = next(m for m in result.ship_marginals if "fewer" in m.label)
    more = next(m for m in result.ship_marginals if "more" in m.label)
    assert fewer.change == "remove" and fewer.node_id in ships_at
    assert fewer.delta_vs_optimal <= 0
    assert more.change == "add" and more.node_id in {"far", "home"}
    assert more.delta_vs_optimal >= 0


def test_ship_marginals_never_suggest_an_inland_node():
    graph = make_graph({"far": ["home"], "home": []}, inland={"far", "home"})
    states = {"far": NodeState(node_id="far", local_value=50.0, player_base_power=5.0),
              "home": NodeState(node_id="home", is_home=True, player_base_power=5.0)}
    config = OptimizeConfig(home_node="home", candidate_nodes=["far", "home"], max_merchants=0, max_light_ships=5)
    result = optimize(graph, states, Params(), config)
    more = next(m for m in result.ship_marginals if "more" in m.label)
    assert more.node_id is None
