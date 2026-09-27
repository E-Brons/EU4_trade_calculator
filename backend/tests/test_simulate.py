"""Toy-network hand-calculated tests for the simulation engine."""
import pytest

from app.engine.model import Allocation, MerchantAction, NodeAllocation, NodeState, Params
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


def test_topo_order_upstream_first():
    graph = make_graph({"a": ["b"], "b": ["c"], "c": []})
    order = graph.topo_order()
    assert order.index("a") < order.index("b") < order.index("c")


def test_single_home_node_collects_everything_no_competition():
    graph = make_graph({"home": []})
    states = {"home": NodeState(node_id="home", local_value=100.0, is_home=True, player_base_power=10.0)}
    alloc = Allocation()
    params = Params(trade_efficiency=0.0)
    result = simulate(graph, states, alloc, params)
    assert result.total_income == pytest.approx(100.0)


def test_home_node_shares_with_competitor():
    graph = make_graph({"home": []})
    states = {
        "home": NodeState(
            node_id="home", local_value=100.0, is_home=True,
            player_base_power=10.0, other_collect_power=30.0,
        )
    }
    result = simulate(graph, states, Allocation(), Params())
    # player power 10 / total 40 = 25% of 100 = 25
    assert result.total_income == pytest.approx(25.0)


def test_upstream_node_forwards_value_to_home_via_steer():
    # "source" produces 100 value with no local competition, all steered by
    # the player's merchant to "home" which the player owns outright.
    graph = make_graph({"source": ["home"], "home": []})
    states = {
        "source": NodeState(node_id="source", local_value=100.0, player_base_power=10.0),
        "home": NodeState(node_id="home", local_value=0.0, is_home=True, player_base_power=5.0),
    }
    alloc = Allocation()
    alloc.nodes["source"] = NodeAllocation(merchant_action=MerchantAction.STEER, steer_target="home")
    params = Params(merchant_power=0.0, steer_value_bonus_per_merchant=0.0)  # isolate the routing logic
    result = simulate(graph, states, alloc, params)
    # source: player power 10 is the only power -> total_power=10, all of it
    # steers to home (not collect) -> full 100 forwarded to home.
    # home: total_value = 0 + 100 = 100, player power 5 is only power -> 100% retained.
    assert result.total_income == pytest.approx(100.0)


def test_passive_power_without_merchant_still_forwards_downstream():
    # No merchant anywhere in "source"; the player's provincial power there
    # is "passive" and should still get forwarded (not collected, since
    # it's not home), landing in "home".
    graph = make_graph({"source": ["home"], "home": []})
    states = {
        "source": NodeState(node_id="source", local_value=100.0, player_base_power=10.0),
        "home": NodeState(node_id="home", local_value=0.0, is_home=True, player_base_power=5.0),
    }
    result = simulate(graph, states, Allocation(), Params())
    assert result.total_income == pytest.approx(100.0)


def test_no_power_penalty_for_collecting_away_from_home():
    # Regression test: TRADE_NON_CAPITAL_OFFICE used to be modeled as a
    # flat 50% trade-power penalty for collecting away from home. The
    # real save refutes this (ragusa/venice collect at full, even
    # slightly boosted, power away from home) -- there must be no power
    # penalty here at all.
    graph = make_graph({"away": []})
    states = {"away": NodeState(node_id="away", local_value=100.0, player_base_power=10.0, other_collect_power=10.0)}
    alloc = Allocation()
    alloc.nodes["away"] = NodeAllocation(merchant_action=MerchantAction.COLLECT)
    params = Params(merchant_power=5.0, trade_efficiency=0.0)
    result = simulate(graph, states, alloc, params)
    # player power = base 10 + merchant_power 5 (no home bonus, not home) = 15
    # total_power = 15 + 10 = 25; share = 15/25 = 0.6
    # merchant present (explicit Collect) -> +0.1 income bonus (TRADE_MERCHANT_PRESENT)
    # income = 100 * 0.6 * (1 + 0 + 0.1) = 66.0
    assert result.total_income == pytest.approx(66.0)


def test_capital_merchant_power_replaces_ordinary_merchant_power_at_home():
    # TRADE_CAPITAL_POWER (5.0) applies instead of the ordinary
    # merchant_power constant when the merchant is stationed at home, and
    # TRADE_POWER_HOME_BONUS (+10%) applies to that added merchant power
    # (not to the base power, which the save already includes it in).
    graph = make_graph({"home": []})
    states = {"home": NodeState(node_id="home", local_value=100.0, is_home=True, player_base_power=10.0)}
    alloc = Allocation()
    alloc.nodes["home"] = NodeAllocation(merchant_action=MerchantAction.COLLECT)
    params = Params(merchant_power=2.0, capital_merchant_power=5.0, home_power_bonus=0.1, trade_efficiency=0.0)
    result = simulate(graph, states, alloc, params)
    # player power = base 10 + (capital_merchant_power 5 * 1.1 home bonus) = 15.5
    # no competition -> share = 1.0; merchant present -> +0.1 income bonus
    # income = 100 * 1.0 * (1 + 0 + 0.1) = 110.0
    assert result.total_income == pytest.approx(110.0)


def test_home_bonus_not_double_counted_on_automatic_capital_collection():
    # With no merchant placed, home_power_bonus must NOT apply to
    # player_base_power at all (it's assumed to already be baked into
    # that base, since it's meant to be read straight from the save's
    # province_power). No merchant present -> no TRADE_MERCHANT_PRESENT
    # bonus either.
    graph = make_graph({"home": []})
    states = {"home": NodeState(node_id="home", local_value=100.0, is_home=True, player_base_power=10.0)}
    params = Params(home_power_bonus=0.1, trade_efficiency=0.0)
    result = simulate(graph, states, Allocation(), params)
    assert result.total_income == pytest.approx(100.0)


def test_trade_efficiency_and_merchant_present_bonus_stack_additively():
    # Confirmed against the real save: TUR's automatic home-node
    # collection (no merchant) realized money at 1.750x its power-weighted
    # value share; its merchant-collected nodes away from home realized
    # 1.8498x-1.8500x -- a +0.10 difference matching TRADE_MERCHANT_PRESENT
    # exactly, and additive with trade_efficiency (not a 1.1x multiplier
    # on top).
    graph = make_graph({"home": [], "away": []})
    states = {
        "home": NodeState(node_id="home", local_value=100.0, is_home=True, player_base_power=10.0),
        "away": NodeState(node_id="away", local_value=100.0, player_base_power=10.0),
    }
    alloc = Allocation()
    alloc.nodes["away"] = NodeAllocation(merchant_action=MerchantAction.COLLECT)
    params = Params(merchant_power=0.0, capital_merchant_power=0.0, home_power_bonus=0.0, trade_efficiency=0.75)
    result = simulate(graph, states, alloc, params)
    assert result.nodes["home"].player_income == pytest.approx(175.0)   # 100 * (1 + 0.75)
    assert result.nodes["away"].player_income == pytest.approx(185.0)   # 100 * (1 + 0.75 + 0.1)


def test_forwarded_value_splits_across_two_links_by_steer_power():
    graph = make_graph({"source": ["home", "rival"], "home": [], "rival": []})
    states = {
        "source": NodeState(
            node_id="source", local_value=90.0,
            other_steer_power={"rival": 20.0},
        ),
        "home": NodeState(node_id="home", is_home=True, player_base_power=1.0),
        "rival": NodeState(node_id="rival", other_collect_power=1.0),
    }
    alloc = Allocation()
    alloc.nodes["source"] = NodeAllocation(merchant_action=MerchantAction.STEER, steer_target="home")
    params = Params(merchant_power=10.0, steer_value_bonus_per_merchant=0.0)
    result = simulate(graph, states, alloc, params)
    # source total_power = 10 (player steer) + 20 (rival steer) = 30
    # home gets 10/30 * 90 = 30, rival gets 20/30*90 = 60
    # home retains all 30 (only power there); rival retains all 60
    assert result.nodes["home"].total_value == pytest.approx(30.0)
    assert result.nodes["rival"].total_value == pytest.approx(60.0)
    assert result.total_income == pytest.approx(30.0)


def test_end_node_with_no_power_wastes_value():
    graph = make_graph({"orphan": []})
    states = {"orphan": NodeState(node_id="orphan", local_value=50.0)}
    result = simulate(graph, states, Allocation(), Params())
    assert result.total_income == pytest.approx(0.0)


def test_steer_with_missing_target_falls_back_to_passive_not_lost():
    # Regression test: a STEER action with no (or an invalid) steer_target
    # must not make that power vanish from the node's value distribution.
    graph = make_graph({"source": ["home"], "home": []})
    states = {
        "source": NodeState(node_id="source", local_value=100.0, player_base_power=10.0),
        "home": NodeState(node_id="home", is_home=True, player_base_power=5.0),
    }
    alloc = Allocation()
    alloc.nodes["source"] = NodeAllocation(merchant_action=MerchantAction.STEER, steer_target=None)
    params = Params(merchant_power=0.0, steer_value_bonus_per_merchant=0.0)
    result = simulate(graph, states, alloc, params)
    # Falls back to passive: same as test_passive_power_without_merchant_still_forwards_downstream.
    assert result.total_income == pytest.approx(100.0)
