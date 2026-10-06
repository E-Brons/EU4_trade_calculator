"""One calculation: structural rules that keep tests, verifier, API and optimizer on the same code path."""
from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"
TRADE = APP / "trade"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            out.add(base)
            out |= {f"{base}.{a.name}" for a in node.names}
    return out


def test_only_calc_imports_game_data():
    offenders = [str(p.relative_to(APP)) for p in APP.rglob("*.py")
                 if p.name not in ("calc.py", "game_data.py") and "app.trade.game_data" in _imports(p)]
    assert not offenders, f"only calc.py may import game constants, found: {offenders}"


def test_calc_is_pure_and_self_contained():
    imports = _imports(TRADE / "calc.py")
    forbidden = {"json", "os", "pathlib", "zipfile", "app.trade.extract", "app.trade.verify", "app.trade.corpus", "app.trade.cases", "app.api", "app.engine"}
    assert not (imports & forbidden), f"calc.py must not touch I/O, extraction or the legacy engine: {imports & forbidden}"
    src = (TRADE / "calc.py").read_text(encoding="utf-8")
    assert "open(" not in src


def test_trade_package_does_not_use_the_legacy_engine():
    offenders = [p.name for p in TRADE.glob("*.py") if any(i.startswith("app.engine") or i.startswith("app.parsing.save") for i in _imports(p))]
    assert not offenders, f"app/trade must not depend on the legacy engine/parser: {offenders}"


def test_verification_runs_the_operational_calculation():
    assert any("calc" in i for i in _imports(TRADE / "verify.py")), "verify.py must call calc.py"
    src = (TRADE / "verify.py").read_text(encoding="utf-8")
    assert "calc.calculate(" in src and "calc.predict_stage(" in src


def test_no_trade_rules_defined_outside_calc():
    offenders = []
    for p in APP.rglob("*.py"):
        if p.name == "calc.py":
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        offenders += [f"{p.relative_to(APP)}:{n.name}" for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name.startswith("rule_")]
    assert not offenders, f"rule_* functions belong in calc.py only: {offenders}"
