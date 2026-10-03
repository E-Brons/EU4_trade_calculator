"""Extracts trade-relevant data from an EU4 `.eu4` save file.

A real `.eu4` is a zip containing `gamestate`, `meta`, and `ai`; Ironman
saves have those members in Paradox's binary format and need melting
first (see `rakaly.py`). We also accept an already-melted flat text file
(not zipped) as produced by pdx.tools' "Melt" button -- meta and gamestate
end up concatenated into one document there, which this module handles
the same way it handles a real save's `gamestate` (the fields we need,
`player=`/`trade={...}`, are present either way).

`gamestate` is huge (tens of MB once melted), so rather than running the
full Clausewitz tokenizer over the whole file we scan for the byte range
of just the top-level `trade={...}` block and tokenize only that.

Field names and the formula they feed are verified against 50 real,
non-Ironman saves, not guessed -- see docs/implementation.md's "Trade
simulation" and "Save parsing" sections for what each field means and the
confirmed relationships between them. Two parsing-specific things worth
knowing: countries in a node are sub-blocks keyed directly by tag
(`TUR={...}`), detected by key shape rather than an allowlist since
colonial/custom tags aren't enumerable in advance; and steering weight is
only given as a node-level aggregate per outgoing link, not per country
(see `_distribute_steer_weights`).
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from app.parsing import rakaly
from app.parsing.clausewitz import as_list, parse

_COUNTRY_TAG_RE = re.compile(r"^[A-Z0-9]{2,4}$")

# Params defaults duplicated here (see engine/model.py) so _player_base_power
# can back out the player's own recorded merchant/ship contribution from
# `val` without importing engine.model at parse time -- keep in sync.
_MERCHANT_POWER_DEFAULT = 2.0
_CAPITAL_MERCHANT_POWER_DEFAULT = 5.0
_POWER_PER_LIGHT_SHIP_DEFAULT = 3.0
_HOME_POWER_BONUS_DEFAULT = 0.1


@dataclass
class ParsedCountryInNode:
    tag: str
    province_power: float = 0.0
    ship_power: float = 0.0
    light_ships: int = 0
    has_capital: bool = False
    has_trader: bool = False
    is_steering: bool = False  # has_trader and a Steer action
    steer_link_index: int = 0  # save's own `steer_power` field: which of the node's outgoing
    # links (0-indexed, same order as ParsedNode.steer_power_weights/graph.outgoing) this
    # country steers to. Absent (default 0) means the first link -- CONFIRMED against a real
    # save: a country with no `steer_power` key always lines up with the node's dominant
    # weight landing on outgoing[0].
    is_collecting: bool = False  # `total` key present on this entry -- the authoritative
    # "actually retains ducats here" signal, CONFIRMED against a real mid-game save: a merchant
    # explicitly Collecting away from the capital gets this (plus nonzero `money`); `has_trader`
    # alone does not -- a save taken before any trade tick has run can have has_trader=True at
    # an away node (a scripted/historical merchant placement) with no `total`/`money` yet, since
    # nothing has been computed there. has_capital always collects regardless of this flag.
    money: float = 0.0  # realized ducats/month from this node, if collecting
    val: float = 0.0  # power-weighted share of the node's WHOLE value (retained + forwarded)
    value_share: float = 0.0  # this country's share of the RETAINED value (per-country `total`
    # field) -- populated whenever is_collecting is True (has_capital, or an away merchant that's
    # actually realized a Collect result). See docs/implementation.md's "Trade simulation"
    # section for the confirmed formula relating this to `val`/`money`.
    add: float = 0.0  # per-country steering-bookkeeping field, refuted as a trade_efficiency
    # proxy -- kept for completeness, not used for anything.
    raw: dict = field(default_factory=dict)

    @property
    def power(self) -> float:
        return self.province_power + self.ship_power


@dataclass
class ParsedNode:
    node_id: str
    local_value: float = 0.0
    total_value: float = 0.0  # save's `total` field: a trade-power-weighted "reach" metric, NOT
    # a ducat figure -- see docs/implementation.md. Used only for the val-sum/retention identity
    # checks in test_real_saves.py, never as a stand-in for ducat value.
    current_value: float = 0.0  # save's `current` field: the node's RETAINED (post-forward)
    # ducat value -- see docs/implementation.md's confirmed formula.
    retention: float = 0.0  # save-reported fraction of gross value retained in-node
    retain_power: float = 0.0  # save's `retain_power` field -- see docs/implementation.md
    pull_power: float = 0.0  # save's `pull_power` field -- see docs/implementation.md
    incoming_sum: float = 0.0  # sum of the save's own `incoming[].value`, read directly rather
    # than accumulated via our own graph traversal (avoids compounding upstream error)
    steer_power_weights: list[float] = field(default_factory=list)  # per outgoing link, save order
    countries: list[ParsedCountryInNode] = field(default_factory=list)


@dataclass
class ParsedSave:
    player_tag: str
    date: str | None = None  # save's in-game date (e.g. "1444.11.11"), for matching test fixtures
    nodes: dict[str, ParsedNode] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    suggested_trade_efficiency: float | None = None
    actual_current_income: float = 0.0
    suggested_max_merchants: int | None = None  # len(countries.<TAG>.merchants.envoy) -- currently
    # DEPLOYED merchants, not the country's merchant cap (that cap isn't stored anywhere in the
    # save; it's computed from tech/ideas). Still a far better starting point than a fixed guess.
    suggested_max_light_ships: int | None = None  # countries.<TAG>.num_subunits_type_and_cat.light_ship.normal


def load_save(path: str | Path, rakaly_path: Path | None = None) -> ParsedSave:
    zpath = Path(path)

    if zipfile.is_zipfile(zpath):
        with zipfile.ZipFile(zpath) as zf:
            names = set(zf.namelist())
            if "gamestate" not in names:
                raise ValueError(f"{zpath.name} doesn't look like an EU4 save (no 'gamestate' member)")
            gamestate_raw = zf.read("gamestate")
            meta_raw = zf.read("meta") if "meta" in names else gamestate_raw

        if rakaly.is_binary(gamestate_raw):
            # Binary Ironman save: melt automatically, with zero manual
            # steps for whoever's uploading (see rakaly.melt_ironman_save
            # for the pdx.tools-automation-then-rakaly-CLI order of
            # attempts). The result is one merged meta+gamestate document,
            # same shape as an already-melted flat text file, so both text
            # vars below point at it.
            melted = rakaly.melt_ironman_save(zpath.read_bytes(), gamestate_raw, rakaly_path)
            merged_text = rakaly.ensure_text(melted, rakaly_path).decode("utf-8", errors="replace")
            gamestate_text = meta_text = merged_text
        else:
            gamestate_text = rakaly.ensure_text(gamestate_raw, rakaly_path).decode("utf-8", errors="replace")
            meta_text = rakaly.ensure_text(meta_raw, rakaly_path).decode("utf-8", errors="replace")
    else:
        # Not a zip: treat as an already-melted flat text document (e.g.
        # pdx.tools' "Melt" output), which has both meta and gamestate
        # fields in one file.
        text = zpath.read_text(encoding="utf-8", errors="replace")
        gamestate_text = text
        meta_text = text

    warnings: list[str] = []
    player_tag = _extract_scalar(meta_text, "player") or _extract_scalar(gamestate_text, "player")
    if not player_tag:
        raise ValueError("Could not find the player's country tag in the save")
    date = _extract_scalar(meta_text, "date") or _extract_scalar(gamestate_text, "date")
    max_merchants, max_light_ships = _extract_player_military(gamestate_text, str(player_tag))

    trade_block_text = extract_top_level_block(gamestate_text, "trade")
    if trade_block_text is None:
        warnings.append("No top-level 'trade' block found in gamestate; falling back to manual entry.")
        return ParsedSave(
            player_tag=player_tag,
            date=date,
            nodes={},
            warnings=warnings,
            suggested_max_merchants=max_merchants,
            suggested_max_light_ships=max_light_ships,
        )

    trade_tree = parse(trade_block_text[1:-1])
    nodes: dict[str, ParsedNode] = {}
    for node_body in as_list(trade_tree.get("node")):
        node_id = node_body.get("definitions")
        if not node_id:
            continue
        parsed = ParsedNode(
            node_id=node_id,
            local_value=_as_float(node_body.get("local_value")),
            total_value=_as_float(node_body.get("total")),
            current_value=_as_float(node_body.get("current")),
            retention=_as_float(node_body.get("retention")),
            retain_power=_as_float(node_body.get("retain_power")),
            pull_power=_as_float(node_body.get("pull_power")),
            incoming_sum=sum(
                _as_float(x.get("value")) for x in as_list(node_body.get("incoming")) if isinstance(x, dict)
            ),
            steer_power_weights=[_as_float(v) for v in as_list(node_body.get("steer_power"))],
        )
        for key, value in node_body.items():
            if not (_COUNTRY_TAG_RE.match(key) and isinstance(value, dict)):
                continue
            has_trader = bool(value.get("has_trader"))
            parsed.countries.append(
                ParsedCountryInNode(
                    tag=key,
                    province_power=_as_float(value.get("province_power")),
                    ship_power=_as_float(value.get("ship_power")),
                    light_ships=int(_as_float(value.get("light_ship"))),
                    has_capital=bool(value.get("has_capital")),
                    has_trader=has_trader,
                    is_steering=has_trader and "type" in value,
                    steer_link_index=int(_as_float(value.get("steer_power"))),
                    is_collecting="total" in value,
                    money=_as_float(value.get("money")),
                    val=_as_float(value.get("val")),
                    value_share=_as_float(value.get("total")),
                    add=_as_float(value.get("add")),
                    raw=value,
                )
            )
        nodes[node_id] = parsed

    if not nodes:
        warnings.append(
            "Parsed a 'trade' block but found no nodes in it -- the parsing "
            "logic in save.py likely needs adjusting for this game version. "
            "Falling back to manual entry."
        )

    # Back-solve trade_efficiency from collecting nodes -- see
    # docs/implementation.md's "Trade simulation" section for the formula.
    MERCHANT_PRESENT_BONUS = 0.1  # TRADE_MERCHANT_PRESENT; keep in sync with engine/model.py Params default
    implied_efficiencies = []
    for node in nodes.values():
        player = next((c for c in node.countries if c.tag == player_tag), None)
        if player and player.money > 0 and player.value_share > 0:
            merchant_bonus = MERCHANT_PRESENT_BONUS if player.has_trader else 0.0
            implied_efficiencies.append(player.money / player.value_share - 1 - merchant_bonus)
    suggested_trade_efficiency = (
        sum(implied_efficiencies) / len(implied_efficiencies) if implied_efficiencies else None
    )

    # The save already computed this exactly (money = realized ducats/month
    # per node); summing it directly beats re-deriving it through
    # simulate()'s necessarily-approximate hypothetical-mode estimate.
    actual_current_income = sum(
        c.money for node in nodes.values() for c in node.countries if c.tag == player_tag
    )

    return ParsedSave(
        player_tag=str(player_tag),
        date=date,
        nodes=nodes,
        warnings=warnings,
        suggested_trade_efficiency=suggested_trade_efficiency,
        actual_current_income=actual_current_income,
        suggested_max_merchants=max_merchants,
        suggested_max_light_ships=max_light_ships,
    )


def build_node_states_from_save(
    parsed: ParsedSave,
    graph,
) -> tuple[dict[str, "NodeState"], dict[str, "NodeAllocation"], str | None, set[str]]:
    """Turns a `ParsedSave` into the engine's `NodeState`/`NodeAllocation`
    inputs, from the player's point of view. `graph` is the loaded
    `TradeGraph` (see `parsing/tradenodes.py`), used to place each node's
    aggregate steer power onto its specific outgoing links.

    See docs/implementation.md's "Trade simulation" section for the
    confirmed collect/steer/passive classification rules and the
    known_* replay fields this populates.
    """
    from app.engine.model import MerchantAction, NodeAllocation, NodeState

    node_states: dict[str, NodeState] = {}
    current_allocation: dict[str, NodeAllocation] = {}
    home_node: str | None = None
    real_presence: set[str] = set()

    for node_id, node in parsed.nodes.items():
        player = next((c for c in node.countries if c.tag == parsed.player_tag), None)
        is_home = bool(player and player.has_capital)
        if is_home:
            home_node = node_id

        other_collect = 0.0
        other_passive = 0.0
        other_steer_total = 0.0
        for c in node.countries:
            if c.tag == parsed.player_tag:
                continue
            if c.is_steering:
                other_steer_total += c.val if c.val else c.power
            elif c.has_capital or c.is_collecting:
                # Home always collects; an away merchant only counts as
                # collecting once it has actually realized a result (see
                # ParsedCountryInNode.is_collecting) -- has_trader alone
                # isn't enough, since a zero-tick save can have a merchant
                # placed but not yet reflected in any recorded value.
                other_collect += c.val if c.val else c.power
            else:
                # `val` is the authoritative value-weight even when
                # province_power/ship_power are 0 (e.g. colonial-range
                # presence with no owned provinces) -- same val-or-power
                # fallback as the branches above, or this country's share
                # of the node's value silently vanishes.
                other_passive += c.val if c.val else c.power

        outgoing = graph.outgoing(node_id) if node_id in graph else ()
        other_steer_power = _distribute_steer_weights(other_steer_total, node.steer_power_weights, outgoing)

        if player:
            if not player.has_trader:
                # No merchant stationed -- NONE even at home (simulate.py's
                # is_home compensation still counts the passive capital
                # collection; this keeps the +10% "merchant present" bonus,
                # which only applies with an actual merchant, from
                # firing here).
                action = MerchantAction.NONE
            elif player.is_steering:
                action = MerchantAction.STEER
            elif player.has_capital or player.is_collecting:
                action = MerchantAction.COLLECT
            else:
                # has_trader with no `type` (not steering) but no realized
                # result yet either (no `total` key) -- a merchant is
                # placed but nothing's been computed for it (zero-tick
                # save). Not COLLECT: there's nothing real to replay here.
                action = MerchantAction.NONE
            steer_target = None
            if action == MerchantAction.STEER and outgoing:
                idx = player.steer_link_index if player.steer_link_index < len(outgoing) else 0
                steer_target = outgoing[idx]
        else:
            action = MerchantAction.NONE
            steer_target = None

        # Authoritative save fields -- only trustworthy for REPLAYING this
        # exact recorded allocation (simulate() gates on
        # NodeState.matches_recorded()), see docs/implementation.md.
        has_known_data = node.retain_power > 0 or node.pull_power > 0

        player_base_power = _player_base_power(player, is_home, node_id, graph)

        node_states[node_id] = NodeState(
            node_id=node_id,
            local_value=node.local_value,
            is_home=is_home,
            player_base_power=player_base_power,
            other_collect_power=other_collect,
            other_steer_power=other_steer_power,
            other_passive_power=other_passive,
            known_gross_value=(node.local_value + node.incoming_sum) if has_known_data else None,
            known_retained_value=node.current_value if has_known_data else None,
            known_retain_power=node.retain_power if has_known_data else None,
            known_pull_power=node.pull_power if has_known_data else None,
            known_player_val=player.val if player else 0.0,
            known_player_action=action,
            known_player_light_ships=player.light_ships if player else 0,
            known_player_steer_target=steer_target,
        )

        if player:
            current_allocation[node_id] = NodeAllocation(
                merchant_action=action,
                steer_target=steer_target,
                light_ships=player.light_ships,
            )
            # Genuine presence -- owned provinces/ships, OR already doing
            # something real here, regardless of `val` (which, after the
            # fix above, can be a small nonzero "colonial range" figure at
            # nodes the player has nothing actually standing in -- not a
            # sane place to suggest a NEW merchant/ship). Raw power is the
            # right signal for "can this candidate be acted on at all",
            # val for "how much is acting on it worth".
            if player.power > 0 or is_home or action != MerchantAction.NONE:
                real_presence.add(node_id)

    return node_states, current_allocation, home_node, real_presence


def _player_base_power(player: "ParsedCountryInNode | None", is_home: bool, node_id: str, graph) -> float:
    """The player's intrinsic trade power at a node, for simulate()'s
    `_player_power` to add merchant/ship bonuses on top of.

    `val` is the authoritative power figure here, for ANY entry (collect,
    steer, or passive) -- CONFIRMED against a real, ticked save two ways:
    summed over has_capital/collecting entries it matches the node's own
    `retain_power`; summed over every OTHER entry (steer + passive
    together) it matches `pull_power`, exactly, for every node without
    meaningful piracy (a handful of colonial/frontier nodes are off by the
    same already-documented pirate-power gap that `test_val_sums_to_node_
    total` tolerates). Earlier reasoning that `val` was unreliable away
    from a collecting entry compared it against raw `province_power+
    ship_power` instead of `pull_power` -- the wrong baseline; `val` was
    right all along, raw power just isn't the same quantity as `val` to
    begin with (val is already-modified; see the ~2x home-vs-away gap at
    collecting entries that raw power alone can't explain either).

    Whatever of `val` is already attributable to the save's OWN recorded
    merchant/ships is subtracted back out first, so a hypothetical
    allocation that changes the merchant/ship count at this node (the
    optimizer's entire job) doesn't double-count the old ones on top of
    the new ones simulate() adds.
    """
    if not player or not player.val:
        # No `val` to work with (e.g. synthetic/manual data, or a
        # genuinely zero-power entry) -- fall back to raw power as-is.
        # Nothing to subtract: unlike `val`, raw power never had the
        # recorded merchant/ship bonus baked into it.
        return player.power if player else 0.0

    recorded_added = 0.0
    if node_id not in graph or not graph.is_inland(node_id):
        recorded_added += player.light_ships * _POWER_PER_LIGHT_SHIP_DEFAULT
    if player.has_trader:
        recorded_added += _CAPITAL_MERCHANT_POWER_DEFAULT if is_home else _MERCHANT_POWER_DEFAULT
    if is_home:
        recorded_added *= 1 + _HOME_POWER_BONUS_DEFAULT

    # Raw power is a floor, not just a 0 clamp: it's never valid for `val`
    # minus its own recorded bonus to come out below the country's bare
    # province/ship power (that would mean the bonus was bigger than the
    # total it's supposedly part of). Falls back to it gracefully instead
    # of collapsing to 0 whenever that happens.
    return max(player.val - recorded_added, player.power)


def _distribute_steer_weights(total: float, weights: list[float], outgoing: tuple[str, ...]) -> dict[str, float]:
    if not outgoing or total <= 0:
        return {}
    if weights and len(weights) == len(outgoing) and sum(weights) > 0:
        return {t: total * (w / sum(weights)) for t, w in zip(outgoing, weights)}
    return {t: total / len(outgoing) for t in outgoing}


def _as_float(value) -> float:
    try:
        return float(value) if value is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def _extract_player_military(gamestate_text: str, player_tag: str) -> tuple[int | None, int | None]:
    """Pulls the player's deployed-merchant count and total light-ship count
    from the top-level `countries={ <TAG>={...} ... }` block, without
    tokenizing the other 1000+ countries in it, and without even scanning
    past our own tag's entry -- `countries` alone is tens of MB, so a naive
    "extract the whole block, then search within it" (like the `trade`
    block above) would burn several seconds walking all of it char-by-char
    just to find its end. `_extract_nested_block` stops the instant it
    finds `player_tag`."""
    country_block = _extract_nested_block(gamestate_text, "countries", player_tag)
    if country_block is None:
        return None, None
    country = parse(country_block[1:-1])
    merchants = country.get("merchants")
    max_merchants = len(as_list(merchants.get("envoy"))) if isinstance(merchants, dict) else 0
    subunits = country.get("num_subunits_type_and_cat")
    light_ship = subunits.get("light_ship") if isinstance(subunits, dict) else None
    max_light_ships = int(_as_float(light_ship.get("normal"))) if isinstance(light_ship, dict) else 0
    return max_merchants, max_light_ships


def _extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"?([^"\n]+?)"?\s*$', text)
    return match.group(1) if match else None


def extract_top_level_block(text: str, key: str) -> str | None:
    """Finds `key={ ... }` at brace-depth 0 and returns the block including
    its braces, without tokenizing the rest of the (potentially huge)
    document. Returns None if the key isn't found at the top level."""
    i = 0
    n = len(text)
    depth = 0
    in_quotes = False
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_quotes = False
            i += 1
            continue
        if c == '"':
            in_quotes = True
            i += 1
            continue
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            brace = _key_eq_brace_at(text, i, key)
            if brace is not None:
                end = _match_brace_block(text, brace)
                if end is not None:
                    return text[brace:end]
        i += 1
    return None


def _extract_nested_block(text: str, outer_key: str, inner_key: str) -> str | None:
    """Like `extract_top_level_block`, but for `outer_key={ inner_key={...}
    ... }` where `outer_key`'s block is too large to fully scan just to
    find its end (e.g. `countries`, tens of MB) -- stops the moment
    `inner_key` is found at depth 1, never walking the rest of
    `outer_key`'s block. Returns None if either key isn't found."""
    n = len(text)
    outer_start = None
    i = 0
    depth = 0
    in_quotes = False
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_quotes = False
            i += 1
            continue
        if c == '"':
            in_quotes = True
            i += 1
            continue
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            brace = _key_eq_brace_at(text, i, outer_key)
            if brace is not None:
                outer_start = brace
                i = brace
                break
        i += 1
    if outer_start is None:
        return None

    # Now scan strictly inside the outer block, tracking depth relative to
    # it (starts at 1, right after its own opening brace), looking for
    # `inner_key={` at depth 1.
    depth = 0
    in_quotes = False
    i = outer_start
    while i < n:
        c = text[i]
        if in_quotes:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_quotes = False
            i += 1
            continue
        if c == '"':
            in_quotes = True
            i += 1
            continue
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            if depth == 0:
                return None  # reached the end of outer_key's block
            i += 1
            continue
        if depth == 1:
            brace = _key_eq_brace_at(text, i, inner_key)
            if brace is not None:
                end = _match_brace_block(text, brace)
                return text[brace:end] if end is not None else None
        i += 1
    return None


def _key_eq_brace_at(text: str, i: int, key: str) -> int | None:
    """If `text[i:]` starts with the bareword `key` (not part of a longer
    identifier) followed by `=` and a `{`, returns the index of that `{`.
    Otherwise None."""
    n = len(text)
    if not (
        text.startswith(key, i)
        and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_"))
        and (i + len(key) >= n or not (text[i + len(key)].isalnum() or text[i + len(key)] == "_"))
    ):
        return None
    j = i + len(key)
    while j < n and text[j] in " \t":
        j += 1
    if j >= n or text[j] != "=":
        return None
    j += 1
    while j < n and text[j] in " \t":
        j += 1
    return j if j < n and text[j] == "{" else None


def _match_brace_block(text: str, start: int) -> int | None:
    """`start` is the index of a `{`. Returns the index just past its
    matching `}` (so `text[start:end]` is the whole `{...}` block),
    handling quoted strings/escapes. None if unterminated."""
    n = len(text)
    depth = 0
    in_quotes = False
    k = start
    while k < n:
        c = text[k]
        if in_quotes:
            if c == "\\":
                k += 2
                continue
            if c == '"':
                in_quotes = False
            k += 1
            continue
        if c == '"':
            in_quotes = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k + 1
        k += 1
    return None
