"""Renders the verification dashboard (stage table, end-to-end chain, edge-case coverage, stored user cases) as markdown."""
from __future__ import annotations

from collections import Counter

from app.trade import calc, corpus, edge_cases


def _table(headers: list[str], rows: list[list]) -> str:
    return "\n".join(["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def stage_table(report: corpus.CorpusReport) -> list[list]:
    rows = []
    for stage in calc.STAGES:
        checks = failures = saves_fail = 0
        status: Counter[str] = Counter()
        for r in report.reports.values():
            s = r.stages[stage]
            status[s.status] += 1
            checks += s.checks
            failures += s.failures
            saves_fail += s.status == "fail"
        verdict = "NOT IMPLEMENTED" if status["not_implemented"] else ("GREEN" if not failures else "RED")
        rows.append([stage, verdict, checks, failures, f"{100 * failures / checks:.2f}%" if checks else "-", f"{saves_fail}/{len(report.reports)}"])
    return rows


def chain_summary(report: corpus.CorpusReport) -> str:
    c = Counter(r.chain.status for r in report.reports.values())
    return ", ".join(f"{k}={v}" for k, v in sorted(c.items()))


def coverage_rows(report: corpus.CorpusReport) -> list[list]:
    manifest_covers = Counter(c for e in report.entries.values() for c in e.get("covers", []))
    rows = []
    for case in edge_cases.CASES:
        n = manifest_covers[case.id] if case.level == "intervention" else sum(1 for r in report.reports.values() if r.edge_cases_present.get(case.id))
        status = ("ABSENT-OK" if n == 0 else "VIOLATED") if case.expect_absent else ("covered" if n else "UNCOVERED")
        rows.append([case.id, case.title, case.level, n, status])
    return rows


def user_case_rows(report: corpus.CorpusReport) -> list[list]:
    rows = []
    for sid, entry in report.entries.items():
        if entry["kind"] == "user_case" and sid in report.reports:
            r = report.reports[sid]
            rows.append([sid, entry["tag"], entry["date"], r.status.upper(), r.first_failing_stage or "-"])
    return rows


def markdown(report: corpus.CorpusReport) -> str:
    reproduced = sum(r.chain.status == "ok" for r in report.reports.values())
    out = [f"# Trade calculation status (calc {calc.CALC_VERSION}, {len(report.reports)} saves)", "",
           f"**Saves reproduced end to end: {reproduced} of {len(report.reports)}**", "", "## Stages", "",
           _table(["stage", "verdict", "checks", "failures", "rate", "saves failing"], stage_table(report)), "",
           f"End-to-end chain: {chain_summary(report)}", ""]
    cases = user_case_rows(report)
    out += ["## Stored user cases", ""]
    out += [_table(["id", "tag", "date", "status", "first failing stage"], cases)] if cases else ["none"]
    out += ["", "## Edge-case coverage", "", _table(["id", "case", "level", "saves exhibiting", "status"], coverage_rows(report))]
    if report.missing:
        out += ["", f"Missing fixtures (no raw file or zip): {', '.join(report.missing)}"]
    return "\n".join(out) + "\n"
