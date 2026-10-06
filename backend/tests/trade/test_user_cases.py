"""Saves stored from user uploads (kind "user_case"). RED until the calculation reproduces them, then flip `expected` to green."""
from __future__ import annotations

import pytest

from app.parsing.tradenodes import load_trade_graph
from app.trade import corpus
from app.trade.extract import extract_world
from app.trade.verify import verify_world

USER_CASES = [e for e in corpus.manifest() if e["kind"] == "user_case"]


@pytest.mark.parametrize("entry", USER_CASES, ids=[e["id"] for e in USER_CASES])
def test_user_case(entry, tmp_path, request):
    path = corpus.locate(entry, tmp_path)
    if path is None:
        pytest.skip(f"{entry['file']} not present (git lfs pull?)")
    if entry["expected"] == "red":
        request.applymarker(pytest.mark.xfail(strict=True, reason=f"RED case, first failing stage was {entry.get('first_failing_stage')}"))
    report = verify_world(extract_world(path, entry["id"], graph=load_trade_graph()))
    assert report.status == "verified", f"{entry['id']}: first failing stage {report.first_failing_stage}; chain {report.chain.status} {report.chain.note}"
