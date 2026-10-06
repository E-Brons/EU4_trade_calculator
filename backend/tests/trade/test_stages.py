"""Every calculation stage against every fixture save (isolated: each stage starts from the save's recorded upstream values).

Failures are grouped by edge case so a RED stage says which situations break it.
"""
from __future__ import annotations

from collections import Counter

import pytest

from app.trade import calc
from tests.trade.expected import EXPECTED_STAGE_STATUS


def stage_verdict(report, stage: str) -> tuple[str, str]:
    stages = [r.stages[stage] for r in report.reports.values()]
    if any(s.status == "not_implemented" for s in stages):
        return "not_implemented", stages[0].note
    failures = sum(s.failures for s in stages)
    checks = sum(s.checks for s in stages)
    if failures == 0:
        return "green", f"{checks} checks"
    by_case: Counter[str] = Counter()
    for s in stages:
        by_case.update(s.failures_by_case)
    worst = sorted((w for r in report.reports.values() for w in r.stages[stage].worst), key=lambda w: -abs(w.predicted - w.recorded))[:8]
    detail = [f"{stage}: {failures}/{checks} checks fail in {sum(s.status == 'fail' for s in stages)}/{len(stages)} saves",
              "failures by edge case: " + ", ".join(f"{c}={n}" for c, n in by_case.most_common(8))]
    detail += [f"  {w.key} {w.node} {w.tag}: calc {w.predicted:.4f} vs save {w.recorded:.4f}" for w in worst]
    return "red", "\n".join(detail)


@pytest.mark.parametrize("stage", calc.STAGES)
def test_stage_status_matches_expectation(stage, full_corpus):
    expected, why = EXPECTED_STAGE_STATUS[stage]
    verdict, detail = stage_verdict(full_corpus, stage)
    assert verdict == expected, (
        f"stage '{stage}' is now {verdict.upper()} but tests/trade/expected.py says {expected.upper()} ({why}).\n{detail}\n"
        "Update expected.py together with the calc.py change that caused this."
    )


@pytest.mark.parametrize("stage", calc.STAGES)
def test_stage_is_green(stage, corpus_report, request):
    expected, why = EXPECTED_STAGE_STATUS[stage]
    if expected != "green":
        request.applymarker(pytest.mark.xfail(strict=True, reason=f"{expected.upper()}: {why}"))
    verdict, detail = stage_verdict(corpus_report, stage)
    assert verdict == "green", detail
