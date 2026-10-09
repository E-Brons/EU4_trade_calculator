"""Every calculation stage against every fixture save (isolated: each stage starts from the save's recorded upstream values).

A stage passes only when every check of every clean save is within the 5% margin (verify.MARGIN); exact failures are
reported alongside. There is no list of accepted failures.
Failures are grouped by edge case so a failing stage says which situations break it.
"""
from __future__ import annotations

from collections import Counter

import pytest

from app.trade import calc


def stage_verdict(report, stage: str) -> tuple[str, str]:
    stages = [r.stages[stage] for r in report.reports.values()]
    if any(s.status == "not_implemented" for s in stages):
        return "not_implemented", stages[0].note
    failures = sum(s.margin_failures for s in stages)
    exact = sum(s.failures for s in stages)
    checks = sum(s.checks for s in stages)
    if failures == 0:
        return "green", f"{checks} checks, all within the 5% margin ({exact} not exact)"
    by_case: Counter[str] = Counter()
    for s in stages:
        by_case.update(s.failures_by_case)
    worst = sorted((w for r in report.reports.values() for w in r.stages[stage].worst), key=lambda w: -abs(w.predicted - w.recorded))[:8]
    detail = [f"{stage}: {failures}/{checks} checks outside the 5% margin ({exact} not exact) in {sum(s.margin_failures > 0 for s in stages)}/{len(stages)} saves",
              "failures by edge case: " + ", ".join(f"{c}={n}" for c, n in by_case.most_common(8))]
    detail += [f"  {w.key} {w.node} {w.tag}: calc {w.predicted:.4f} vs save {w.recorded:.4f}" for w in worst]
    return "red", "\n".join(detail)


@pytest.mark.parametrize("stage", calc.STAGES)
def test_stage_is_green(stage, corpus_report):
    verdict, detail = stage_verdict(corpus_report, stage)
    assert verdict == "green", detail
