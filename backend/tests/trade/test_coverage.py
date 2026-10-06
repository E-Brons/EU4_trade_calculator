"""Every edge case must be exercised by at least one fixture; the uncovered set is an explicit, shrinking ledger."""
from __future__ import annotations

from collections import Counter

from app.trade import edge_cases
from tests.trade.expected import KNOWN_UNCOVERED


def coverage(report) -> dict[str, int]:
    manifest_covers = Counter(c for e in report.entries.values() for c in e.get("covers", []))
    counts: dict[str, int] = {}
    for case in edge_cases.CASES:
        if case.level == "intervention":
            counts[case.id] = manifest_covers[case.id]
        else:
            counts[case.id] = sum(1 for r in report.reports.values() if r.edge_cases_present.get(case.id))
    return counts


def test_uncovered_edge_cases_equal_the_known_ledger(full_corpus):
    counts = coverage(full_corpus)
    uncovered = {c.id for c in edge_cases.CASES if not c.expect_absent and counts[c.id] == 0}
    new_gaps = sorted(uncovered - KNOWN_UNCOVERED)
    closed = sorted(KNOWN_UNCOVERED - uncovered)
    assert not new_gaps, f"edge cases with no fixture and not in KNOWN_UNCOVERED: {new_gaps}"
    assert not closed, f"edge cases now covered; remove from KNOWN_UNCOVERED in tests/trade/expected.py: {closed}"


def test_assumption_guards_never_occur(full_corpus):
    counts = coverage(full_corpus)
    violated = [c.id for c in edge_cases.CASES if c.expect_absent and counts[c.id] > 0]
    assert not violated, f"cases that must never occur were found in a save: {violated} (our assumption is wrong)"


def test_every_case_has_unique_id_and_known_research_task():
    from pathlib import Path
    ids = [c.id for c in edge_cases.CASES]
    assert len(ids) == len(set(ids))
    tasks = {p.name.split("_")[0] for p in (Path(__file__).resolve().parents[3] / "docs" / "research").glob("R*_goal.md")}
    unknown = [(c.id, r) for c in edge_cases.CASES for r in c.research if r not in tasks]
    assert not unknown, f"edge cases reference research tasks that do not exist: {unknown}"
