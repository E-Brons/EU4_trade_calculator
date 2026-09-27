from app.parsing.tradenodes import load_trade_graph


def test_generated_tradenodes_has_80_nodes():
    graph = load_trade_graph()
    assert len(graph.nodes) == 80


def test_graph_is_acyclic_topo_order_covers_all_nodes():
    graph = load_trade_graph()
    order = graph.topo_order()
    assert set(order) == set(graph.nodes)
    assert len(order) == len(set(order))


def test_topo_order_respects_edges():
    graph = load_trade_graph()
    position = {n: i for i, n in enumerate(graph.topo_order())}
    for node_id, info in graph.nodes.items():
        for target in info.outgoing:
            assert position[node_id] < position[target], f"{node_id} -> {target} out of order"


def test_every_node_reaches_an_end_node():
    graph = load_trade_graph()
    assert set(graph.end_nodes) == {n for n, info in graph.nodes.items() if not info.outgoing}
    for node_id in graph.nodes:
        cur = node_id
        seen = {cur}
        while graph.outgoing(cur):
            cur = graph.outgoing(cur)[0]
            assert cur not in seen, f"cycle reached from {node_id}"
            seen.add(cur)
        assert cur in graph.end_nodes


def test_upstream_path_to_home_found_for_known_pair():
    graph = load_trade_graph()
    path = graph.upstream_path_to("constantinople", "venice")
    assert path is not None
    assert path[0] == "constantinople"
    assert path[-1] == "venice"


def test_nodes_upstream_of_excludes_home_itself():
    graph = load_trade_graph()
    upstream = graph.nodes_upstream_of("venice")
    assert "venice" not in upstream
    assert "constantinople" in upstream
