"""Loads the trade node graph (data/tradenodes.json) and exposes topology
helpers: outgoing edges, topological order, and reachability."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "tradenodes.json"


@dataclass(frozen=True)
class TradeNodeInfo:
    node_id: str
    display_name: str
    inland: bool
    outgoing: tuple[str, ...]


class TradeGraph:
    def __init__(self, raw: dict):
        self.game_version: str = raw["game_version"]
        self.end_nodes: list[str] = raw["end_nodes"]
        self.nodes: dict[str, TradeNodeInfo] = {}
        for node_id, body in raw["nodes"].items():
            self.nodes[node_id] = TradeNodeInfo(
                node_id=node_id,
                display_name=body["display_name"],
                inland=body["inland"],
                outgoing=tuple(o["target"] for o in body["outgoing"]),
            )
        self._topo_order = self._compute_topo_order()

    def __contains__(self, node_id: str) -> bool:
        return node_id in self.nodes

    def outgoing(self, node_id: str) -> tuple[str, ...]:
        return self.nodes[node_id].outgoing

    def is_inland(self, node_id: str) -> bool:
        return self.nodes[node_id].inland

    def display_name(self, node_id: str) -> str:
        return self.nodes[node_id].display_name

    def topo_order(self) -> list[str]:
        """Node ids ordered so that every node appears before any node it
        sends trade value to (upstream/source nodes first, end nodes
        last)."""
        return self._topo_order

    def _compute_topo_order(self) -> list[str]:
        # Kahn's algorithm over the "sends value to" edges (outgoing).
        indegree = {n: 0 for n in self.nodes}
        for n, info in self.nodes.items():
            for target in info.outgoing:
                indegree[target] += 1

        ready = [n for n, d in indegree.items() if d == 0]
        ready.sort()
        order: list[str] = []
        while ready:
            n = ready.pop(0)
            order.append(n)
            for target in self.nodes[n].outgoing:
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
            ready.sort()

        if len(order) != len(self.nodes):
            remaining = set(self.nodes) - set(order)
            raise ValueError(f"Trade node graph has a cycle involving: {remaining}")
        return order

    def upstream_path_to(self, start: str, home: str, max_hops: int = 12) -> list[str] | None:
        """Breadth-first search for a downstream path of node ids from
        `start` to `home` following outgoing edges (used to seed the
        heuristic: nodes upstream of home should steer toward it)."""
        from collections import deque

        if start == home:
            return [start]
        visited = {start}
        queue: deque[list[str]] = deque([[start]])
        while queue:
            path = queue.popleft()
            if len(path) > max_hops:
                continue
            for nxt in self.outgoing(path[-1]):
                if nxt in visited:
                    continue
                new_path = path + [nxt]
                if nxt == home:
                    return new_path
                visited.add(nxt)
                queue.append(new_path)
        return None

    def nodes_upstream_of(self, home: str) -> set[str]:
        """All nodes that have some directed path (via outgoing edges) to
        `home`, i.e. candidates that could usefully steer toward it."""
        reverse: dict[str, list[str]] = {n: [] for n in self.nodes}
        for n, info in self.nodes.items():
            for target in info.outgoing:
                reverse[target].append(n)

        seen = {home}
        stack = [home]
        while stack:
            cur = stack.pop()
            for pred in reverse[cur]:
                if pred not in seen:
                    seen.add(pred)
                    stack.append(pred)
        seen.discard(home)
        return seen


@lru_cache(maxsize=1)
def load_trade_graph() -> TradeGraph:
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return TradeGraph(raw)
