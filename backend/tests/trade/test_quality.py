"""Save-quality classifier: which saves can be required to match exactly (R12 final: trade is computed on the 1st)."""
from __future__ import annotations

from app.trade import quality
from app.trade.types import WorldInputs


def test_timing():
    assert quality.timing("1444.11.11", "1444.11.11") == quality.PRE_FIRST_TICK      # bookmark, nothing computed yet
    assert quality.timing("1444.11.30", "1444.11.11") == quality.PRE_FIRST_TICK
    assert quality.timing("1444.12.1", "1444.11.11") == quality.TICK_DAY             # first computation
    assert quality.timing("1444.12.2", "1444.11.11") == quality.MID_MONTH
    assert quality.timing("1445.1.1", "1444.12.15") == quality.TICK_DAY               # year rollover of the first 1st
    assert quality.timing("1444.12.1", "1444.12.1") == quality.PRE_FIRST_TICK          # a start on a 1st: first computation is a month later
    assert quality.timing("garbage", "1444.11.11") == quality.UNKNOWN


def test_mods_and_dlc_keys():
    assert quality.mods_key(()) == "vanilla"
    assert quality.mods_key(("Bigger UI V1.37", "Medieval music")) == "vanilla"          # cosmetic allowlist
    assert quality.mods_key(("b", "a")) == quality.mods_key(("a", "b"))
    assert quality.mods_key(("a",)).startswith("mods-") and len(quality.mods_key(("a",))) == 13
    assert quality.mods_key(("a", "Medieval music")) == quality.mods_key(("a",))
    assert quality.dlc_key(("Rights of Man", "Art of War")) == quality.dlc_key(("Art of War", "Rights of Man"))


def _inputs(**kw) -> WorldInputs:
    base = dict(game_version="1.37.5", date="1445.4.1", player="VEN", nodes={}, entries={}, node_order=(), multipliers={},
                start_date="1444.11.11")
    return WorldInputs(**(base | kw))


def test_clean_requires_tick_day_supported_version_and_nothing_of_ours_on_the_way():
    assert quality.classify(_inputs()).clean
    assert not quality.classify(_inputs(date="1445.4.2")).clean
    assert not quality.classify(_inputs(own_merchants_in_transit=1)).clean
    assert not quality.classify(_inputs(own_fleets_in_transit=1)).clean
    assert not quality.classify(_inputs(game_version="1.36.0")).clean
