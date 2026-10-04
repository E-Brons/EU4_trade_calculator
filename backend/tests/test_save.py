import zipfile
from pathlib import Path

import pytest

from app.engine.model import MerchantAction
from app.parsing import ironman_melt, pdx_tools_browser, pdx_tools_melt
from app.parsing.save import build_node_states_from_save, extract_top_level_block, load_save
from app.parsing.tradenodes import TradeGraph

# Structure verified against a real melted 1.37.5 save: countries are
# sub-blocks keyed directly by tag (TUR=, VEN=), not a repeated
# `country={tag=...}` block.
GAMESTATE = b"""EU4txt
date=1444.11.11
player="TUR"
some_other_block={
\tnested=1
}
trade={
\tnode={
\t\tdefinitions="ragusa"
\t\tlocal_value=5.0
\t\ttotal=10.0
\t\tsteer_power=1.000
\t\tTUR={
\t\t\tval=3.0
\t\t\tmax_pow=4.0
\t\t\tmax_demand=0.75
\t\t\tprovince_power=3.0
\t\t\tship_power=1.0
\t\t\tlight_ship=2
\t\t\thas_capital=yes
\t\t}
\t\tVEN={
\t\t\tprovince_power=7.0
\t\t\thas_trader=yes
\t\t}
\t}
\tnode={
\t\tdefinitions="venice"
\t\tlocal_value=2.0
\t\ttotal=2.0
\t}
}
after_trade=1
"""

META = b'EU4txt\nplayer="TUR"\n'


def make_fake_save(tmp_path: Path) -> Path:
    save_path = tmp_path / "fake.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", GAMESTATE)
        zf.writestr("meta", META)
        zf.writestr("ai", b"")
    return save_path


def test_extract_top_level_block_finds_trade_only():
    text = GAMESTATE.decode()
    block = extract_top_level_block(text, "trade")
    assert block is not None
    assert block.startswith("trade={") is False  # block excludes the key, starts at "{"
    assert block.startswith("{")
    assert '"ragusa"' in block
    assert "some_other_block" not in block


def test_extract_top_level_block_missing_key_returns_none():
    text = GAMESTATE.decode()
    assert extract_top_level_block(text, "does_not_exist") is None


def test_load_save_parses_player_and_nodes(tmp_path):
    save_path = make_fake_save(tmp_path)
    parsed = load_save(save_path)
    assert parsed.player_tag == "TUR"
    assert set(parsed.nodes) == {"ragusa", "venice"}
    ragusa = parsed.nodes["ragusa"]
    assert ragusa.local_value == 5.0
    assert ragusa.total_value == 10.0
    assert ragusa.steer_power_weights == [1.0]
    tags = {c.tag for c in ragusa.countries}
    assert tags == {"TUR", "VEN"}
    tur = next(c for c in ragusa.countries if c.tag == "TUR")
    assert tur.province_power == 3.0
    assert tur.light_ships == 2
    assert tur.has_capital is True
    ven = next(c for c in ragusa.countries if c.tag == "VEN")
    assert ven.has_trader is True
    assert ven.is_steering is False  # has_trader but no "type" key => not steering (see
    # build_node_states_from_save: without has_capital too, this does NOT mean "collecting"
    # -- confirmed against real saves, see test_build_node_states_from_save_identifies_home_and_collect_vs_steer)
    assert parsed.warnings == []


def test_load_save_accepts_unzipped_flat_text(tmp_path):
    # pdx.tools' "Melt" button downloads a flat (non-zip) text file with
    # meta + gamestate fields merged into one document.
    flat_path = tmp_path / "melted.eu4"
    flat_path.write_bytes(GAMESTATE)
    parsed = load_save(flat_path)
    assert parsed.player_tag == "TUR"
    assert set(parsed.nodes) == {"ragusa", "venice"}


def test_suggested_trade_efficiency_backsolved_from_money_and_value_share(tmp_path):
    # trade_efficiency is back-solved from collecting nodes via
    # money = value_share * (1 + trade_efficiency + merchant_present_bonus
    # [0.1 iff has_trader]), where value_share is the per-country `total`
    # field (the country's share of *retained* value -- NOT `val`, which
    # spans the whole node's retained+forwarded value and is a different,
    # larger number). See save.py's derivation comment. The old `add`
    # field was refuted as a trade_efficiency proxy and is no longer used.
    gamestate = b"""EU4txt
player="TUR"
trade={
\tnode={
\t\tdefinitions="ragusa"
\t\ttotal=1.0
\t\tTUR={
\t\t\tval=100.0
\t\t\ttotal=8.0
\t\t\tmoney=10.0
\t\t\thas_capital=yes
\t\t}
\t}
\tnode={
\t\tdefinitions="venice"
\t\ttotal=1.0
\t\tTUR={
\t\t\tval=200.0
\t\t\ttotal=16.0
\t\t\tmoney=20.0
\t\t\thas_trader=yes
\t\t}
\t}
}
"""
    save_path = tmp_path / "eff.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", gamestate)
        zf.writestr("meta", META)
    parsed = load_save(save_path)
    # ragusa (no merchant): 10/8 - 1 - 0    = 0.25
    # venice (merchant):    20/16 - 1 - 0.1 = 0.15
    assert parsed.suggested_trade_efficiency == pytest.approx((0.25 + 0.15) / 2)


def test_actual_current_income_is_exact_sum_of_money_field(tmp_path):
    # This is the save's own already-computed number, used as ground
    # truth for "current income" instead of re-deriving it through
    # simulate()'s (necessarily estimated) formula.
    gamestate = b"""EU4txt
player="TUR"
trade={
\tnode={
\t\tdefinitions="ragusa"
\t\ttotal=1.0
\t\tTUR={
\t\t\tval=8.0
\t\t\tmoney=10.0
\t\t\thas_capital=yes
\t\t}
\t}
\tnode={
\t\tdefinitions="venice"
\t\ttotal=1.0
\t\tTUR={
\t\t\tval=16.0
\t\t\tmoney=20.0
\t\t\thas_trader=yes
\t\t}
\t}
\tnode={
\t\tdefinitions="ancona"
\t\ttotal=1.0
\t\tVEN={
\t\t\tval=5.0
\t\t\tmoney=99.0
\t\t}
\t}
}
"""
    save_path = tmp_path / "income.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", gamestate)
        zf.writestr("meta", META)
    parsed = load_save(save_path)
    assert parsed.actual_current_income == pytest.approx(30.0)  # only TUR's money, not VEN's


def _toy_graph() -> TradeGraph:
    return TradeGraph({
        "game_version": "test",
        "end_nodes": ["venice"],
        "nodes": {
            "ragusa": {"display_name": "Ragusa", "inland": False, "outgoing": [{"target": "venice"}]},
            "venice": {"display_name": "Venice", "inland": False, "outgoing": []},
        },
    })


def test_build_node_states_from_save_identifies_home_and_collect_vs_steer(tmp_path):
    save_path = make_fake_save(tmp_path)
    parsed = load_save(save_path)
    graph = _toy_graph()

    node_states, current_allocation, home_node, real_presence = build_node_states_from_save(parsed, graph)

    assert home_node == "ragusa"
    assert node_states["ragusa"].is_home is True
    assert node_states["ragusa"].player_base_power == 3.0  # max_pow(4.0) - ship_power(1.0) --
    # see _player_base_power: everything about this country's power at this node EXCEPT its own
    # ships, read directly off the save rather than reconstructed from province_power + a
    # guessed merchant/home bonus (there's a real "bonus" of 0.0 to find here -- max_pow(4.0)
    # - province_power(3.0) - ship_power(1.0) -- but that's coincidental to this fixture's
    # made-up numbers, not a general "province+ship" identity).
    # CONFIRMED against 35 real 1444.11.11 saves (23,275 per-country trade-node
    # entries, zero exceptions): a `power_fraction`/`money`/paid-out share only
    # ever appears on the has_capital entry. `has_trader=yes` alone (no
    # capital, no explicit steer) never comes with one -- so VEN here (no
    # `has_capital`) is passive, not a collector, regardless of `has_trader`.
    assert node_states["ragusa"].other_collect_power == 0.0
    assert node_states["ragusa"].other_passive_power == 7.0
    assert current_allocation["ragusa"].merchant_action == MerchantAction.NONE  # home, no merchant
    assert current_allocation["ragusa"].light_ships == 2
    assert real_presence == {"ragusa"}  # genuine presence (home); venice has none for TUR


# --- Automatic melting of binary Ironman saves ----------------------------
#
# These mock the heavy part (the pdx.tools file-bridge round trip) so they
# run fast and deterministically. A real, unmocked end-to-end run against
# the live Ironman save fixture lives in test_api.py, guarded to skip when
# pdx.tools/a melt worker aren't actually reachable (as is the case in this
# sandbox).

BINARY_MAGIC_GAMESTATE = b"EU4bin\x00not real binary tokens, pdx_tools_melt.melt is mocked below"


def make_fake_ironman_save(tmp_path: Path) -> Path:
    save_path = tmp_path / "ironman.eu4"
    with zipfile.ZipFile(save_path, "w") as zf:
        zf.writestr("gamestate", BINARY_MAGIC_GAMESTATE)
        zf.writestr("meta", b"EU4bin\x00also fake")
        zf.writestr("ai", b"")
    return save_path


def _unavailable_in_process_melt(*a, **kw):
    raise RuntimeError("playwright/chromium not available in this test environment")


def test_load_save_melts_binary_via_pdx_tools_bridge(tmp_path, monkeypatch):
    save_path = make_fake_ironman_save(tmp_path)

    # In-process browser automation is tried first (see
    # ironman_melt.melt_ironman_save); simulate it being unavailable here
    # (as it is in this sandboxed test run) so the fallback to a separate
    # worker-bridge process below gets exercised.
    monkeypatch.setattr(pdx_tools_browser, "melt_via_browser", _unavailable_in_process_melt)
    monkeypatch.setattr(pdx_tools_melt, "available", lambda *a, **kw: True)
    monkeypatch.setattr(pdx_tools_melt, "melt", lambda file_bytes, *a, **kw: GAMESTATE)

    parsed = load_save(save_path)
    assert parsed.player_tag == "TUR"
    assert set(parsed.nodes) == {"ragusa", "venice"}


def test_load_save_raises_actionable_error_when_no_melt_path_available(tmp_path, monkeypatch):
    save_path = make_fake_ironman_save(tmp_path)

    monkeypatch.setattr(pdx_tools_browser, "melt_via_browser", _unavailable_in_process_melt)
    monkeypatch.setattr(pdx_tools_melt, "available", lambda *a, **kw: False)

    with pytest.raises(ironman_melt.MeltUnavailableError) as exc_info:
        load_save(save_path)
    message = str(exc_info.value)
    assert "pdx.tools" in message
    assert "melt_worker.py" in message
    assert "manually" in message

