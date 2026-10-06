"""Compares the calculation (calc.py) with what the save recorded, stage by stage and end to end.

Used by the tests, the CLI report and the upload API, so all three judge the calculation the same way.
Tolerances equal the save's display rounding (three decimals; products of two rounded fields get a relative term).
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field

from app.parsing.tradenodes import load_trade_graph
from app.trade import calc, edge_cases
from app.trade.types import UnknownVariable, World

# (absolute, relative) tolerance per stage; see module docstring. Wider than rounding only where a product of two
# rounded fields is compared.
TOLERANCE: dict[str, tuple[float, float]] = {
    "val": (0.0005, 0.0),              # fixed-point truncation reproduces the stored value exactly; 0.0005 is float noise
    "income_share": (0.0005, 0.0),
    "income_efficiency": (0.002, 0.001),   # the efficiency itself is observed with unknown decimals
    "link_flow": (0.002, 0.002),
}
DEFAULT_TOLERANCE = (0.002, 0.001)
CHAIN_TOLERANCE = (0.01, 0.003)


def close(predicted: float, recorded: float, abs_tol: float, rel_tol: float) -> bool:
    return abs(predicted - recorded) <= max(abs_tol, rel_tol * abs(recorded))


@dataclass
class Failure:
    key: str
    node: str
    tag: str
    predicted: float
    recorded: float
    cases: tuple[str, ...]


@dataclass
class StageReport:
    stage: str
    status: str                                  # ok | fail | not_implemented
    checks: int = 0
    failures: int = 0
    max_abs_error: float = 0.0
    worst: list[Failure] = field(default_factory=list)
    failures_by_case: dict[str, int] = field(default_factory=dict)
    checks_by_case: dict[str, int] = field(default_factory=dict)
    note: str = ""


@dataclass
class ChainReport:
    status: str                                  # ok | fail | unknown_variable
    note: str = ""
    player_income_calculated: float | None = None
    player_income_recorded: float = 0.0
    checks: int = 0
    failures: int = 0
    worst: list[Failure] = field(default_factory=list)


@dataclass
class VerificationReport:
    save_id: str
    player: str
    date: str
    calc_version: str
    game_version: str
    stages: dict[str, StageReport]
    chain: ChainReport
    edge_cases_present: dict[str, int]
    unmapped_keys: dict[str, int]

    @property
    def status(self) -> str:
        stages_ok = all(s.status == "ok" for s in self.stages.values())
        return "verified" if stages_ok and self.chain.status == "ok" else "mismatch"

    @property
    def first_failing_stage(self) -> str | None:
        for name in calc.STAGES:
            s = self.stages.get(name)
            if s and s.status != "ok":
                return name
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status
        d["first_failing_stage"] = self.first_failing_stage
        return d


def _classify(ctx, node: str, tag: str) -> tuple[str, ...]:
    cases = set(edge_cases.classify_node(ctx, node))
    e = ctx.world.inputs.entries.get((node, tag)) if tag else None
    if e is not None:
        cases |= edge_cases.classify_entry(ctx, e)
    return tuple(sorted(cases))


def verify_stage(stage: str, world: World, ctx, max_worst: int = 10) -> StageReport:
    try:
        pairs = calc.predict_stage(stage, world)
    except calc.NotImplementedStage as e:
        return StageReport(stage, "not_implemented", note=str(e))
    abs_tol, rel_tol = TOLERANCE.get(stage, DEFAULT_TOLERANCE)
    report = StageReport(stage, "ok")
    by_case_fail: Counter[str] = Counter()
    by_case_all: Counter[str] = Counter()
    bad: list[Failure] = []
    for p in pairs:
        cases = _classify(ctx, p.node, p.tag)
        by_case_all.update(cases)
        report.checks += 1
        if not close(p.predicted, p.recorded, abs_tol, rel_tol):
            report.failures += 1
            report.max_abs_error = max(report.max_abs_error, abs(p.predicted - p.recorded))
            by_case_fail.update(cases)
            bad.append(Failure(p.key, p.node, p.tag, p.predicted, p.recorded, cases))
    bad.sort(key=lambda f: -abs(f.predicted - f.recorded))
    report.worst = bad[:max_worst]
    report.failures_by_case = dict(by_case_fail)
    report.checks_by_case = dict(by_case_all)
    report.status = "ok" if report.failures == 0 else "fail"
    return report


def verify_chain(world: World, max_worst: int = 10) -> ChainReport:
    """The whole world from raw inputs (calc.calculate) against the recorded node values and every collector's money."""
    observed = calc.identify_observed(world)
    recorded_income = sum(r.money or 0.0 for (n, t), r in world.recorded.entries.items() if t == world.inputs.player)
    try:
        result = calc.calculate(world.inputs, world.inputs.decisions, observed)
    except UnknownVariable as e:
        return ChainReport("unknown_variable", note=str(e), player_income_recorded=recorded_income)
    abs_tol, rel_tol = CHAIN_TOLERANCE
    chain = ChainReport("ok", player_income_calculated=result.income(world.inputs.player), player_income_recorded=recorded_income)
    bad: list[Failure] = []
    for node, nr in world.recorded.nodes.items():
        if nr.current is not None and node in result.nodes:
            chain.checks += 1
            if not close(result.nodes[node].current, nr.current, abs_tol, rel_tol):
                chain.failures += 1
                bad.append(Failure("current", node, "", result.nodes[node].current, nr.current, ()))
    for (node, tag), r in world.recorded.entries.items():
        if r.money is not None and (node, tag) in result.entries:
            chain.checks += 1
            if not close(result.entries[(node, tag)].money, r.money, abs_tol, rel_tol):
                chain.failures += 1
                bad.append(Failure("money", node, tag, result.entries[(node, tag)].money, r.money, ()))
    chain.checks += 1
    if not close(chain.player_income_calculated, recorded_income, abs_tol, rel_tol):
        chain.failures += 1
    bad.sort(key=lambda f: -abs(f.predicted - f.recorded))
    chain.worst = bad[:max_worst]
    chain.status = "ok" if chain.failures == 0 else "fail"
    return chain


def verify_world(world: World, stages: tuple[str, ...] = calc.STAGES, with_chain: bool = True) -> VerificationReport:
    ctx = edge_cases.make_ctx(world, load_trade_graph())
    return VerificationReport(
        save_id=world.save_id,
        player=world.inputs.player,
        date=world.inputs.date,
        calc_version=calc.CALC_VERSION,
        game_version=world.inputs.game_version,
        stages={s: verify_stage(s, world, ctx) for s in stages},
        chain=verify_chain(world) if with_chain else ChainReport("ok", note="skipped"),
        edge_cases_present=edge_cases.present_cases(ctx),
        unmapped_keys=dict(world.unmapped_keys),
    )
