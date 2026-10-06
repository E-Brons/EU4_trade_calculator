"""Writes docs/trade_spec.md from the code. Usage (from backend/): python3 scripts/gen_spec.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.trade.spec import render_spec  # noqa: E402

OUT = Path(__file__).resolve().parent.parent.parent / "docs" / "trade_spec.md"

if __name__ == "__main__":
    OUT.write_text(render_spec(), encoding="utf-8")
    print(f"wrote {OUT}")
