"""docs/trade_spec.md is generated from the code; fail when the committed copy is stale."""
from __future__ import annotations

from pathlib import Path

from app.trade.spec import render_spec

SPEC = Path(__file__).resolve().parents[3] / "docs" / "trade_spec.md"


def test_committed_spec_is_up_to_date():
    assert SPEC.exists(), "run: python3 scripts/gen_spec.py (from backend/)"
    assert SPEC.read_text(encoding="utf-8") == render_spec(), "docs/trade_spec.md is stale: run python3 scripts/gen_spec.py (from backend/)"
