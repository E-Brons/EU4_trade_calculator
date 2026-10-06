"""The variable registry is complete: nothing in a save's trade block is unknown to us ("obscured variable" detector)."""
from __future__ import annotations

from pathlib import Path

from app.trade import calc, game_data, variables


def test_no_unmapped_keys_in_any_save(corpus_report):
    bad = {sid: r.unmapped_keys for sid, r in corpus_report.reports.items() if r.unmapped_keys}
    assert not bad, (
        "the trade block contains keys that variables.py does not know (a possible missing variable). Add each to the registry "
        f"(kind, meaning, research task) before the calculation can be trusted: {bad}"
    )


def test_registry_is_consistent():
    ids = [v.id for v in variables.VARIABLES]
    assert len(ids) == len(set(ids)), "duplicate variable ids"
    kinds = {"constant", "read", "observed", "recorded", "ignored", "unknown"}
    assert all(v.kind in kinds for v in variables.VARIABLES)
    missing = [i for i in list(variables.NODE_KEYS.values()) + list(variables.ENTRY_KEYS.values()) if i not in set(ids)]
    assert not missing, f"key maps point at undefined variables: {missing}"
    bad_stage = [(v.id, s) for v in variables.VARIABLES for s in v.stages if s not in calc.STAGES]
    assert not bad_stage, f"variables reference unknown stages: {bad_stage}"
    tasks = {p.name.split("_")[0] for p in (Path(__file__).resolve().parents[3] / "docs" / "research").glob("R*_goal.md")}
    bad_task = [(v.id, r) for v in variables.VARIABLES for r in v.research if r not in tasks]
    assert not bad_task, f"variables reference research tasks that do not exist: {bad_task}"


def test_every_constant_variable_exists_in_vendored_game_data():
    for v in variables.VARIABLES:
        if v.kind == "constant":
            game_data.const(v.id)   # KeyError if missing


def test_every_stage_has_a_variable_and_every_input_is_used():
    used = {s for v in variables.VARIABLES for s in v.stages}
    assert not [s for s in calc.STAGES if s not in used and s != "multiplier"], "stage without any registered variable"
    context_only = {"player", "mods", "dlcs", "ironman", "node_id"}   # identify the save / feed edge cases, no stage consumes them
    unused_inputs = [v.id for v in variables.VARIABLES if v.kind in ("read", "observed") and not v.stages and not v.research and v.id not in context_only]
    assert not unused_inputs, f"input variables neither used by a stage nor assigned to a research task: {unused_inputs}"
