"""Registry of every variable the calculation touches or the save contains.

kind:
  constant  - from the game's own files (game_data.py)
  read      - raw input read from the save
  observed  - input read from the save whose derivation from modifiers is not computed yet (docs/research)
  recorded  - result the game stored; used only to verify our calculation, never as calculation input
  ignored   - key known and deliberately unused (reason given)
  unknown   - meaning not established (research task given)

tests/trade/test_variables.py fails if a save contains a trade-block key that is not mapped here: that is how a
missing ("obscured") variable surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Variable:
    id: str
    kind: str
    description: str
    save_path: str = ""
    stages: tuple[str, ...] = ()
    research: tuple[str, ...] = ()


def _v(id, kind, description, save_path="", stages=(), research=()):
    return Variable(id, kind, description, save_path, tuple(stages), tuple(research))


VARIABLES: tuple[Variable, ...] = (
    # --- world ---
    _v("game_version", "read", "savegame_version first.second.third", "savegame_version", research=("R12",)),
    _v("date", "read", "in-game date of the save", "date", research=("R12",)),
    _v("player", "read", "player country tag", "player"),
    _v("mods", "read", "enabled mods (edge case: a non-cosmetic mod can change trade)", "mods_enabled_names"),
    _v("dlcs", "read", "enabled DLC", "dlc_enabled"),
    _v("ironman", "read", "save was a binary Ironman save melted by pdx.tools"),
    _v("trade_efficiency", "observed", "country trade efficiency, identified at the country's collecting nodes (not stored in the save)",
       "trade.node[].<tag>.money / .total", ("income_efficiency",), ("R07",)),
    _v("steering_strength", "observed", "country's steering strength: add = trunc3(strength / rank) on each link, identified from the add values (not stored)",
       "trade.node[].<tag>.add", ("steer_weights",), ("R08",)),
    _v("merchant_power", "observed", "country's flat power on every entry with a merchant (0 in start saves), identified from max_pow minus its known parts",
       "trade.node[].<tag>.max_pow", ("raw_power",), ("R06",)),
    # --- node: read ---
    _v("node_id", "read", "trade node id", "trade.node[].definitions"),
    _v("local_value", "read", "node's own production value (ducats)", "trade.node[].local_value", ("link_flow", "current_value"), ("R13",)),
    _v("trade_company_region", "read", "node is a trade company region", "trade.node[].trade_company_region", (), ("R04",)),
    # --- node: recorded ---
    _v("node_current", "recorded", "retained ducat value", "trade.node[].current", ("current_value",)),
    _v("node_outgoing", "recorded", "forwarded ducat value", "trade.node[].outgoing", ("link_flow",)),
    _v("node_value_added_outgoing", "recorded", "forwarded value incl. steering bonus (equals outgoing in all fixtures)", "trade.node[].value_added_outgoing", (), ("R08",)),
    _v("node_retention", "recorded", "fraction of gross value retained", "trade.node[].retention", ("retention",)),
    _v("node_retain_power", "recorded", "sum of effective power of collectors", "trade.node[].retain_power", ("retain_power", "retention")),
    _v("node_pull_power", "recorded", "sum of effective power of pulling non-collectors (absent at end nodes)", "trade.node[].pull_power", ("pull_power", "retention"), ("R03",)),
    _v("node_total", "recorded", "sum of all country val (not ducats)", "trade.node[].total", (), ("R10",)),
    _v("node_steer_weights", "recorded", "one weight per outgoing link in graph edge order", "trade.node[].steer_power", ("steer_weights", "link_flow"), ("R08",)),
    _v("node_incoming", "recorded", "flows received per upstream node: value, add, from (1-based node index)", "trade.node[].incoming", ("link_flow",), ("R08",)),
    _v("node_num_collectors", "recorded", "number of collectors", "trade.node[].num_collectors", (), ("R10",)),
    _v("node_num_collectors_incl_pirates", "recorded", "number of collectors including pirates", "trade.node[].num_collectors_including_pirates", (), ("R10",)),
    _v("node_collector_power", "unknown", "equals retain_power in all nodes checked", "trade.node[].collector_power", (), ("R09",)),
    _v("node_collector_power_incl_pirates", "unknown", "collector power including pirates", "trade.node[].collector_power_including_pirates", (), ("R10",)),
    _v("node_p_pow", "unknown", "meaning unknown", "trade.node[].p_pow", (), ("R09",)),
    _v("node_max", "unknown", "meaning unknown", "trade.node[].max", (), ("R09",)),
    _v("node_highest_power", "unknown", "meaning unknown", "trade.node[].highest_power", (), ("R09",)),
    _v("node_trade_goods_size", "ignored", "per-goods production sizes; display only (see R13 if local_value is ever recomputed)", "trade.node[].trade_goods_size"),
    _v("node_top_provinces", "ignored", "display: top provincial powers", "trade.node[].top_provinces"),
    _v("node_top_provinces_values", "ignored", "display", "trade.node[].top_provinces_values"),
    _v("node_top_power", "ignored", "display: sorted countries by val", "trade.node[].top_power"),
    _v("node_top_power_values", "ignored", "display", "trade.node[].top_power_values"),
    _v("node_treasure_ship_passage", "ignored", "date of last treasure fleet passage; not part of the formula (revisit in R10)", "trade.node[].most_recent_treasure_ship_passage"),
    # --- entry: read ---
    _v("province_power", "read", "country's province trade power in the node", "<tag>.province_power", ("propagation", "raw_power"), ("R05", "R13")),
    _v("ship_power", "read", "power of the country's light ships assigned to the node", "<tag>.ship_power", ("raw_power",), ("R11",)),
    _v("light_ships", "read", "number of light ships assigned to the node", "<tag>.light_ship", ("raw_power",), ("R11",)),
    _v("has_capital", "read", "country's capital is in this node", "<tag>.has_capital", ("raw_power", "retain_power"), ("R06",)),
    _v("has_trader", "read", "a merchant is present", "<tag>.has_trader", ("raw_power", "income_efficiency"), ("R06", "R07")),
    _v("steering", "read", "merchant steers (key `type` present)", "<tag>.type", ("pull_power", "steer_weights"), ("R08",)),
    _v("steer_link", "read", "index of the outgoing link steered/pulled to (absent = first)", "<tag>.steer_power", ("steer_weights",), ("R08",)),
    _v("collecting", "read", "game marks the country as collecting here (key `total` present)", "<tag>.total", ("retain_power", "pull_power"), ("R03",)),
    _v("t_out", "read", "power transferred out", "<tag>.t_out", ("transfers", "retain_power", "pull_power"), ("R04",)),
    _v("t_in", "read", "power transferred in", "<tag>.t_in", ("transfers", "retain_power", "pull_power"), ("R04",)),
    _v("t_to", "read", "receivers of transferred power", "<tag>.t_to", ("transfers",), ("R04",)),
    _v("t_from", "read", "givers of transferred power", "<tag>.t_from", (), ("R04",)),
    _v("modifier", "read", "node-level modifier blocks (merchant_recalled, pirate_hunting, ...)", "<tag>.modifier", ("raw_power",), ("R06",)),
    _v("multiplier", "observed", "max_demand: multiplier from max_pow to val; includes the away-from-capital penalty", "<tag>.max_demand", ("multiplier", "val"), ("R01", "R02")),
    # --- entry: recorded ---
    _v("entry_prev", "recorded", "power propagated in", "<tag>.prev", ("propagation", "raw_power"), ("R05",)),
    _v("entry_max_pow", "recorded", "province + ship + prev + extras", "<tag>.max_pow", ("raw_power", "val"), ("R06",)),
    _v("entry_val", "recorded", "max_pow * max_demand", "<tag>.val", ("val", "retain_power", "pull_power")),
    _v("entry_money", "recorded", "monthly ducats of a collector", "<tag>.money", ("income_efficiency",), ("R07",)),
    _v("entry_share_total", "recorded", "collector's share of retained ducats", "<tag>.total", ("income_share",), ("R07",)),
    _v("entry_power_fraction", "recorded", "collector's share of retained power", "<tag>.power_fraction", (), ("R07",)),
    _v("entry_add", "observed", "steering value bonus on the steered link (size not derived)", "<tag>.add", ("link_flow",), ("R08",)),
    _v("entry_potential", "recorded", "net transferred power / node total, signed (R04, verified)", "<tag>.potential", ("transfers",), ("R04", "R09")),
    _v("entry_already_sent", "unknown", "meaning unknown", "<tag>.already_sent", (), ("R09",)),
    # --- constants (game_data) ---
    _v("TRADE_CAPITAL_POWER", "constant", "flat power at the capital node", "defines.lua", ("raw_power",), ("R06",)),
    _v("MERCHANT_MAX_POWER_BONUS", "constant", "flat power of a merchant (not used: the data show a per-country merchant power, see merchant_power)", "defines.lua", (), ("R06",)),
    _v("FIXED_POINT_SCALE", "constant", "game values are 3-decimal fixed point, truncated (fitted, data/game/empirical.json)", "empirical", ("val", "income_share", "income_efficiency", "transfers"), ("R04",)),
    _v("TRANSFER_FRACTION", "constant", "share a subject transfers to its overlord (fitted)", "empirical", ("transfers",), ("R04",)),
    _v("TRANSFER_MIN_POWER_KEPT", "constant", "subtracted from val before the transfer fraction (fitted, origin unexplained)", "empirical", ("transfers",), ("R04",)),
    _v("TRADE_NON_CAPITAL_OFFICE", "constant", "away-collection factor is 1 + this (-0.5)", "defines.lua", ("multiplier",), ("R02",)),
    _v("TRADE_PROPAGATE_DIVIDER", "constant", "propagation divisor", "defines.lua", ("propagation",), ("R05",)),
    _v("TRADE_PROPAGATE_THRESHOLD", "constant", "propagation threshold", "defines.lua", ("propagation",), ("R05",)),
    _v("TRADE_MERCHANT_PRESENT", "constant", "income bonus when a merchant is present", "defines.lua", ("income_efficiency",), ("R07",)),
    _v("TRADE_ADDED_VALUE_MODIFER", "constant", "steering value bonus", "defines.lua", ("link_flow",), ("R08",)),
)

BY_ID = {v.id: v for v in VARIABLES}

# trade.node[] key -> variable id
NODE_KEYS: dict[str, str] = {
    "definitions": "node_id",
    "local_value": "local_value",
    "trade_company_region": "trade_company_region",
    "current": "node_current",
    "outgoing": "node_outgoing",
    "value_added_outgoing": "node_value_added_outgoing",
    "retention": "node_retention",
    "retain_power": "node_retain_power",
    "pull_power": "node_pull_power",
    "total": "node_total",
    "steer_power": "node_steer_weights",
    "incoming": "node_incoming",
    "num_collectors": "node_num_collectors",
    "num_collectors_including_pirates": "node_num_collectors_incl_pirates",
    "collector_power": "node_collector_power",
    "collector_power_including_pirates": "node_collector_power_incl_pirates",
    "p_pow": "node_p_pow",
    "max": "node_max",
    "highest_power": "node_highest_power",
    "trade_goods_size": "node_trade_goods_size",
    "top_provinces": "node_top_provinces",
    "top_provinces_values": "node_top_provinces_values",
    "top_power": "node_top_power",
    "top_power_values": "node_top_power_values",
    "most_recent_treasure_ship_passage": "node_treasure_ship_passage",
}

# trade.node[].<TAG> key -> variable id
ENTRY_KEYS: dict[str, str] = {
    "province_power": "province_power",
    "ship_power": "ship_power",
    "light_ship": "light_ships",
    "has_capital": "has_capital",
    "has_trader": "has_trader",
    "type": "steering",
    "steer_power": "steer_link",
    "total": "entry_share_total",
    "t_out": "t_out",
    "t_in": "t_in",
    "t_to": "t_to",
    "t_from": "t_from",
    "modifier": "modifier",
    "max_demand": "multiplier",
    "prev": "entry_prev",
    "max_pow": "entry_max_pow",
    "val": "entry_val",
    "money": "entry_money",
    "power_fraction": "entry_power_fraction",
    "add": "entry_add",
    "potential": "entry_potential",
    "already_sent": "entry_already_sent",
}
