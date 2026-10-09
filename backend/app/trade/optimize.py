"""Search for the player's merchant and light-ship placement with the highest trade income.

Every candidate placement is priced by calc.WhatIf (the same calculation the verifier checks against real saves);
this module only searches. Decisions per candidate node: a merchant action (none / collect / steer to one of the
node's outgoing links) and a number of light ships (sea nodes only).

  1. Seed: a merchant collecting at home, the others steering along the shortest path towards home, ships greedily
     (the save's own placement, when given, is searched from as well, so the result is never worse than it).
  2. Fill any merchants left one at a time with the best single addition.
  3. Local search: change one node's merchant action at a time while income rises, re-place the ships; a few random
     restarts from perturbed seeds.
  4. Marginals: what one merchant / one chunk of ships more or fewer would be worth, and where.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.parsing.tradenodes import TradeGraph
from app.trade.calc import WhatIf
from app.trade.types import Action, NodeDecision

MAX_LOCAL_SEARCH_ROUNDS = 8   # merchant 1-opt and ship re-placement can nudge each other between near-ties forever
Placement = dict[str, NodeDecision]


@dataclass
class OptimizeConfig:
    home_node: str
    candidate_nodes: list[str]
    max_merchants: int
    max_light_ships: int
    random_seed: int = 0
    max_restarts: int = 3
    ship_chunk: int = 0          # light ships moved per step; 0 = about 1/20 of the fleet (at least 1)
    starts: list[Placement] = field(default_factory=list)   # extra starting points (the save's own placement)


@dataclass
class Marginal:
    """Income with one merchant / one chunk of ships more or fewer than the optimum, and where that change is made
    (node_id; None when no placement helps or there is nothing to take away)."""

    label: str
    income: float
    delta_vs_optimal: float
    node_id: str | None = None
    change: str | None = None            # "add" | "remove"
    action: Action | None = None
    steer_target: str | None = None


@dataclass
class OptimizeResult:
    placement: Placement
    income: float
    baseline_income: float               # no merchant and no ship anywhere
    merchant_marginals: list[Marginal] = field(default_factory=list)
    ship_marginals: list[Marginal] = field(default_factory=list)
    evaluations: int = 0


def _copy(p: Placement) -> Placement:
    return dict(p)


def _set(p: Placement, node: str, action: Action | None = None, target: str | None = None, ships: int | None = None) -> Placement:
    cur = p.get(node, NodeDecision())
    a = cur.action if action is None else action
    t = (cur.steer_target if action is None else target) if a == Action.STEER else None
    out = _copy(p)
    out[node] = NodeDecision(a, t, cur.light_ships if ships is None else ships)
    return out


def merchants_used(p: Placement) -> int:
    return sum(1 for d in p.values() if d.action != Action.NONE)


def ships_used(p: Placement) -> int:
    return sum(d.light_ships for d in p.values())


class Optimizer:
    def __init__(self, what_if: WhatIf, graph: TradeGraph, config: OptimizeConfig):
        self.wi, self.graph, self.cfg = what_if, graph, config
        candidates = [n for n in config.candidate_nodes if n in graph]
        if config.home_node in graph and config.home_node not in candidates:
            candidates.insert(0, config.home_node)
        self.candidates = candidates
        self.sea = [n for n in candidates if not graph.is_inland(n)]
        self.chunk = config.ship_chunk or max(1, config.max_light_ships // 20)
        self.evaluations = 0
        self._cache: dict[tuple, float] = {}

    def score(self, p: Placement) -> float:
        key = tuple(sorted((n, d.action.value, d.steer_target, d.light_ships) for n, d in p.items() if d.action != Action.NONE or d.light_ships))
        if key not in self._cache:
            self.evaluations += 1
            self._cache[key] = self.wi.income(p)
        return self._cache[key]

    def options(self, node: str) -> list[tuple[Action, str | None]]:
        return [(Action.NONE, None), (Action.COLLECT, None), *[(Action.STEER, t) for t in self.graph.outgoing(node)]]

    # ---------------------------------------------------------------------------------------------------- ships

    def place_ships(self, p: Placement, budget: int) -> Placement:
        """Greedy: one chunk at a time where it adds most; then single-ship moves between nodes while they help."""
        p = {n: NodeDecision(d.action, d.steer_target, 0) for n, d in p.items()}
        if not self.sea or budget <= 0:
            return p
        income, left = self.score(p), budget
        while left > 0:
            step = min(self.chunk, left)
            best = max(((self.score(_set(p, n, ships=p.get(n, NodeDecision()).light_ships + step)), n) for n in self.sea))
            if best[0] <= income + 1e-9:
                break
            income, p, left = best[0], _set(p, best[1], ships=p.get(best[1], NodeDecision()).light_ships + step), left - step
        if self.chunk > 1:
            improved = True
            while improved:
                improved = False
                for src in [n for n in self.sea if p.get(n, NodeDecision()).light_ships >= 1]:
                    for dst in self.sea:
                        if dst == src:
                            continue
                        trial = _set(_set(p, src, ships=p[src].light_ships - 1), dst, ships=p.get(dst, NodeDecision()).light_ships + 1)
                        s = self.score(trial)
                        if s > income + 1e-9:
                            income, p, improved = s, trial, True
                            break
                    if improved:
                        break
        return p

    # ---------------------------------------------------------------------------------------------------- merchants

    def seed(self) -> Placement:
        p: Placement = {}
        left = self.cfg.max_merchants
        home = self.cfg.home_node
        if left > 0 and home in self.graph:
            p = _set(p, home, Action.COLLECT)
            left -= 1
        for node in self.candidates:
            if node == home or left <= 0:
                continue
            path = self.graph.upstream_path_to(node, home)
            if path and len(path) >= 2:
                p = _set(p, node, Action.STEER, path[1])
                left -= 1
        return self.place_ships(p, self.cfg.max_light_ships)

    def refine(self, p: Placement) -> Placement:
        while merchants_used(p) > self.cfg.max_merchants:   # a perturbed seed may exceed the budget
            base = self.score(p)
            loss, node = min((base - self.score(_set(p, n, Action.NONE)), n) for n, d in p.items() if d.action != Action.NONE)
            p = _set(p, node, Action.NONE)
        while merchants_used(p) < self.cfg.max_merchants:
            base = self.score(p)
            trials = [(self.score(_set(p, n, a, t)), n, a, t) for n in self.candidates if p.get(n, NodeDecision()).action == Action.NONE
                      for a, t in self.options(n) if a != Action.NONE]
            if not trials:
                break
            best = max(trials, key=lambda x: x[0])
            if best[0] <= base + 1e-9:
                break
            p = _set(p, best[1], best[2], best[3])
        for _ in range(MAX_LOCAL_SEARCH_ROUNDS):
            changed = False
            income = self.score(p)
            for node in self.candidates:
                cur = p.get(node, NodeDecision())
                for a, t in self.options(node):
                    if (a, t) == (cur.action, cur.steer_target if cur.action == Action.STEER else None):
                        continue
                    if a != Action.NONE and cur.action == Action.NONE and merchants_used(p) >= self.cfg.max_merchants:
                        continue
                    trial = _set(p, node, a, t)
                    s = self.score(trial)
                    if s > income + 1e-9:
                        income, p, cur, changed = s, trial, trial[node], True
            reshipped = self.place_ships(p, self.cfg.max_light_ships)
            if self.score(reshipped) > income + 1e-9:
                p, changed = reshipped, True
            if not changed:
                break
        return p

    def perturb(self, p: Placement, rng: random.Random) -> Placement:
        for _ in range(min(2, len(self.candidates))):
            node = rng.choice(self.candidates)
            a, t = rng.choice(self.options(node))
            p = _set(p, node, a, t)
        return p

    def run(self) -> OptimizeResult:
        rng = random.Random(self.cfg.random_seed)
        baseline = self.score({})
        seed = self.seed()
        best, best_income = None, float("-inf")
        starts = [seed] + [self.perturb(seed, rng) for _ in range(self.cfg.max_restarts)] + [
            {n: d for n, d in start.items() if n in self.candidates} for start in self.cfg.starts]
        for start in starts:
            p = self.refine(start)
            s = self.score(p)
            if s > best_income:
                best, best_income = p, s
        best = {n: d for n, d in (best or {}).items() if d.action != Action.NONE or d.light_ships}
        return OptimizeResult(best, best_income, baseline, self.merchant_marginals(best, best_income),
                              self.ship_marginals(best, best_income), self.evaluations)

    # ---------------------------------------------------------------------------------------------------- marginals

    def merchant_marginals(self, best: Placement, income: float) -> list[Marginal]:
        fewer = Marginal("one fewer merchant", income, 0.0)
        removals = [(self.score(_set(best, n, Action.NONE)), n) for n, d in best.items() if d.action != Action.NONE]
        if removals:
            s, n = max(removals)
            fewer = Marginal("one fewer merchant", s, s - income, n, "remove", best[n].action, best[n].steer_target)
        more = Marginal("one more merchant", income, 0.0)
        adds = [(self.score(_set(best, n, a, t)), n, a, t) for n in self.candidates if best.get(n, NodeDecision()).action == Action.NONE
                for a, t in self.options(n) if a != Action.NONE]
        if adds:
            s, n, a, t = max(adds, key=lambda x: x[0])
            if s > income + 1e-9:
                more = Marginal("one more merchant", s, s - income, n, "add", a, t)
        return [fewer, more]

    def ship_marginals(self, best: Placement, income: float) -> list[Marginal]:
        c = self.chunk
        fewer = Marginal(f"{c} fewer light ships", income, 0.0)
        removals = [(self.score(_set(best, n, ships=d.light_ships - c)), n) for n, d in best.items() if d.light_ships >= c]
        if removals:
            s, n = max(removals)
            fewer = Marginal(fewer.label, s, s - income, n, "remove")
        more = Marginal(f"{c} more light ships", income, 0.0)
        adds = [(self.score(_set(best, n, ships=best.get(n, NodeDecision()).light_ships + c)), n) for n in self.sea]
        if adds:
            s, n = max(adds)
            if s > income + 1e-9:
                more = Marginal(more.label, s, s - income, n, "add")
        return [fewer, more]


def optimize(what_if: WhatIf, graph: TradeGraph, config: OptimizeConfig) -> OptimizeResult:
    return Optimizer(what_if, graph, config).run()
