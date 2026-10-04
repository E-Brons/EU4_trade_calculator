"""Validates the *formula* (not the replay shortcut) against real, ticked
saves -- saves that were actually played, not just a game-start snapshot.

Every "start" fixture in tests/fixtures/saves.json (kind="start") is the
game's opening state, saved before unpausing: no ships, no transfers, no AI
decisions ever reach the trade block there (see test_real_saves.py's module
docstring). So test_simulator_reproduces_saves_own_numbers, which has
always run green against all of them, never once exercised a nonzero ship
count or a non-capital collector. This file's saves are "ticked" (kind=
"ticked" in the manifest): real, actively-played saves, which do have those
things -- see docs/implementation.md's "Trade simulation" section and
docs/test.md for how they were made.

The key trick: `build_node_states_from_save` and `suggested_trade_efficiency_for`
both take an arbitrary tag, not just the save's own recorded player. So
every country present in a ticked save's trade nodes -- not just the one
human player -- becomes a free, independent real-data test case by relabeling
it "the player" and checking whether the *formula* (not the replay shortcut)
reproduces that country's own recorded numbers. One ticked save with ~80
nodes and dozens of countries yields hundreds of real (node, country, role,
ship-count) combinations this way, across home/collecting/steering/passive
roles and a wide range of ship counts -- see the printed per-category tally
in test_every_country_reproduces_its_own_power's failure output.

This deliberately calls the exact same engine entry point
(`app.engine.simulate.simulate`) that `/api/simulate` and the optimizer use
-- there is no separate "test formula", because a parallel implementation
in test code could silently drift from what the app actually ships (see the
plan at hand: calibration_offset existed and nobody looked at it).
"""
from __future__ import annotations

import dataclasses
from collections import Counter
from pathlib import Path

import pytest

from app.engine.model import Allocation, MerchantAction, Params
from app.engine.simulate import simulate
from app.parsing.save import build_node_states_from_save, load_save, suggested_trade_efficiency_for
from app.parsing.tradenodes import load_trade_graph

from tests.test_real_saves import MANIFEST, NODE_ABS_TOL, NODE_REL_TOL, TOTAL_ABS_TOL, TOTAL_REL_TOL, _save_path

TICKED = [e for e in MANIFEST if e.get("kind") == "ticked"]

# Power: tightest tolerance we can defend -- save-side display rounding is ~0.001, and every
# power check in this file is now exact to that (no approximation left to excuse a miss).
POWER_REL_TOL = 0.005
POWER_ABS_TOL = 0.01
# Income: reuses test_real_saves.py's existing, already-justified tolerance (see its own
# comment) rather than inventing a stricter one -- the residual gap here is the SAME already-
# documented approximation (`trade_efficiency` is one constant per country, back-solved as an
# average across every node it collects at; an individual node can deviate from that average),
# not something this file's fix is responsible for closing further.
INCOME_REL_TOL = NODE_REL_TOL
INCOME_ABS_TOL = NODE_ABS_TOL


def _role(country) -> str:
    if country.has_capital:
        return "home"
    if country.is_steering:
        return "steer"
    if country.is_collecting:
        return "collect"
    return "passive"


def _rel_close(actual: float, expected: float, rel_tol: float, abs_tol: float) -> bool:
    return abs(actual - expected) <= max(rel_tol * abs(expected), abs_tol)


@pytest.fixture(params=TICKED, ids=[e["id"] for e in TICKED])
def ticked_save(request, tmp_path):
    entry = request.param
    path = _save_path(entry, tmp_path)
    if path is None or not path.exists():
        pytest.skip(f"ticked fixture save not present: {entry['file']} (see docs/test.md)")
    graph = load_trade_graph()
    parsed = load_save(path)
    return entry, graph, parsed


def test_every_country_reproduces_its_own_power(ticked_save):
    """For every country present in a ticked save's trade nodes, relabel it
    "the player" and check that simulate()'s player_power/player_income --
    the formula path the optimizer actually runs, not the is_replay
    shortcut -- reproduce that country's own recorded val/money at every
    node it's in. Failures are grouped by (role, has_ships) so a RED run
    tells you exactly which situations the formula gets wrong, not just
    that it's wrong somewhere."""
    entry, graph, parsed = ticked_save

    tags = sorted({c.tag for node in parsed.nodes.values() for c in node.countries if c.val > 0 or c.power > 0})
    assert tags, f"{entry['id']}: no countries with any trade presence -- fixture is empty"

    failures: list[str] = []
    tally: Counter[tuple[str, bool]] = Counter()
    checked = 0

    for tag in tags:
        as_this_country = dataclasses.replace(parsed, player_tag=tag)
        node_states, current_allocation, _home, _presence = build_node_states_from_save(as_this_country, graph)
        trade_efficiency = suggested_trade_efficiency_for(parsed.nodes, tag)
        params = Params(trade_efficiency=trade_efficiency or 0.0)
        allocation = Allocation(nodes=dict(current_allocation))
        result = simulate(graph, node_states, allocation, params)

        for node_id, node in parsed.nodes.items():
            country = next((c for c in node.countries if c.tag == tag), None)
            if country is None or (country.val <= 0 and country.power <= 0):
                continue
            if node_id not in result.nodes:
                continue
            breakdown = result.nodes[node_id]
            role = _role(country)
            has_ships = country.light_ships > 0
            checked += 1
            tally[(role, has_ships)] += 1

            if not _rel_close(breakdown.player_power, country.net_power, POWER_REL_TOL, POWER_ABS_TOL):
                failures.append(
                    f"{entry['id']}/{node_id}/{tag} ({role}, ships={country.light_ships}): "
                    f"player_power={breakdown.player_power:.3f} != save val(net of transfers)={country.net_power:.3f}"
                )
                continue  # power is already wrong; a downstream income check would be redundant noise

            if country.is_collecting and country.money > 0:
                if not _rel_close(breakdown.player_income, country.money, INCOME_REL_TOL, INCOME_ABS_TOL):
                    failures.append(
                        f"{entry['id']}/{node_id}/{tag} ({role}, ships={country.light_ships}): "
                        f"player_income={breakdown.player_income:.3f} != save money={country.money:.3f}"
                    )

    assert checked > 0, f"{entry['id']}: no (node, country) combinations with real presence to check"

    if failures:
        summary = ", ".join(f"{role}{'+ships' if ships else ''}={n}" for (role, ships), n in sorted(tally.items()))
        pytest.fail(
            f"{entry['id']}: {len(failures)}/{checked} (node, country) combinations failed "
            f"(checked by category: {summary}):\n" + "\n".join(failures[:40])
            + (f"\n... and {len(failures) - 40} more" if len(failures) > 40 else "")
        )


def test_current_case_matches_save(ticked_save):
    """The formula, applied to the save's own recorded allocation, must
    reproduce the save's own recorded total income -- exactly the check
    behind the mismatch warning (see app.engine.validate, once it exists).
    Unlike test_simulator_reproduces_saves_own_numbers, this never takes
    the is_replay shortcut: Params carries no known_* fields here because
    we go through the same node_states the live app builds for a real
    import, so simulate() has no choice but to run the formula."""
    entry, graph, parsed = ticked_save
    node_states, current_allocation, _home, _presence = build_node_states_from_save(parsed, graph)
    params = Params(trade_efficiency=parsed.suggested_trade_efficiency or 0.0)
    allocation = Allocation(nodes=dict(current_allocation))
    result = simulate(graph, node_states, allocation, params)

    assert _rel_close(result.total_income, parsed.actual_current_income, TOTAL_REL_TOL, TOTAL_ABS_TOL), (
        f"{entry['id']}: formula total_income={result.total_income:.2f} != "
        f"save actual_current_income={parsed.actual_current_income:.2f}"
    )
