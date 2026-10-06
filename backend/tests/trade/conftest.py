from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.trade import corpus, report as report_module


def partial_corpus() -> bool:
    return bool(os.environ.get("EU4_FIXTURE_IDS"))


@pytest.fixture(scope="session")
def corpus_report():
    entries = corpus.selected()
    if not entries:
        pytest.skip("no fixture saves selected")
    result = corpus.run_corpus(entries)
    if not result.reports:
        pytest.skip("no fixture saves available (raw files or tracked zips)")
    out = os.environ.get("VERIFY_OUT")
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        (Path(out) / "stage-report.md").write_text(report_module.markdown(result), encoding="utf-8")
        (Path(out) / "stage-report.json").write_text(json.dumps({k: v.to_dict() for k, v in result.reports.items()}, indent=1), encoding="utf-8")
    return result


@pytest.fixture(scope="session")
def full_corpus(corpus_report):
    if partial_corpus() or corpus_report.missing:
        pytest.skip("partial corpus (EU4_FIXTURE_IDS set or fixtures missing): corpus-wide expectations not checked")
    return corpus_report
