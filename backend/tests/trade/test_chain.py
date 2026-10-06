"""calc.calculate (whole world from raw inputs, no recorded values) against every recorded node value and collector income."""
from __future__ import annotations

import pytest

from tests.trade.expected import EXPECTED_CHAIN


def chain_verdict(report) -> tuple[str, str]:
    chains = [r.chain for r in report.reports.values()]
    bad = [(sid, r.chain) for sid, r in report.reports.items() if r.chain.status != "ok"]
    if not bad:
        return "green", f"{len(chains)} saves"
    lines = [f"end-to-end chain fails in {len(bad)}/{len(chains)} saves"]
    for sid, c in bad[:12]:
        if c.status == "unknown_variable":
            lines.append(f"  {sid}: {c.note}")
        else:
            lines.append(f"  {sid}: player income calc {c.player_income_calculated:.3f} vs save {c.player_income_recorded:.3f}; {c.failures}/{c.checks} checks fail")
    return "red", "\n".join(lines)


def test_chain_status_matches_expectation(full_corpus):
    verdict, detail = chain_verdict(full_corpus)
    assert verdict == EXPECTED_CHAIN, f"chain is now {verdict.upper()}, expected {EXPECTED_CHAIN.upper()}.\n{detail}\nUpdate tests/trade/expected.py."


def test_chain_is_green(corpus_report, request):
    if EXPECTED_CHAIN != "green":
        request.applymarker(pytest.mark.xfail(strict=True, reason="end-to-end chain is RED until every stage is green"))
    verdict, detail = chain_verdict(corpus_report)
    assert verdict == "green", detail
