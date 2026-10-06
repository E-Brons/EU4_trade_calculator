"""calc.calculate (whole world from raw inputs, no recorded values) against every recorded node value and collector income.

This is the measure of correctness: it passes only when every save is reproduced end to end."""
from __future__ import annotations


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


def test_chain_is_green(corpus_report):
    verdict, detail = chain_verdict(corpus_report)
    assert verdict == "green", detail
