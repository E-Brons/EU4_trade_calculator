#!/usr/bin/env python3
"""Edit merchants and light-ship trade missions in a plain-text (non-Ironman) EU4 1.37.5 save.

Evidence: tools/EU4-game-automation/MERCHANTS_SHIPS.md (Venice series U25/U27/U28/U29). Only the fields listed below are
touched; everything else stays byte-identical. Derived values (val, max_pow incl. the merchant term, add, ship_power,
steer weights, transfer flows) are NOT recomputed: the game recomputes them on the next 1st of the month (R12).
So: patch, load, run to the next 1st, save.

    from savepatch import place_merchant, recall_merchant, set_light_ship_mission
    text = place_merchant(text, "VEN", "ragusa", "steer", "venice")

CLI:
    savepatch.py in.eu4 out.eu4 place VEN ragusa steer venice
    savepatch.py in.eu4 out.eu4 place VEN genua collect
    savepatch.py in.eu4 out.eu4 recall VEN ragusa
    savepatch.py in.eu4 out.eu4 ships VEN alexandria            # move the tag's light-ship-only fleet there
    savepatch.py in.eu4 out.eu4 ships VEN alexandria --navy-id 234

Status (2026-10-06): written from save evidence, NOT yet loaded into the game. Items marked GUESS are untested.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

GRAPH = Path(__file__).resolve().parents[2] / "backend" / "data" / "tradenodes.json"
# light-ship unit types: common/units/*.txt with type = light_ship (vanilla 1.37.5)
LIGHT_SHIP_TYPES = {"barque", "caravel", "early_frigate", "frigate", "great_frigate", "heavy_frigate"}


class PatchError(ValueError):
    pass


# ------------------------------------------------------------------ text helpers
def _block_end(t: str, brace: int) -> int:
    """index just after the '}' matching t[brace] == '{' (no braces occur inside quoted strings in these blocks)."""
    d = 0
    for j in range(brace, len(t)):
        c = t[j]
        if c == "{":
            d += 1
        elif c == "}":
            d -= 1
            if d == 0:
                return j + 1
    raise PatchError("unbalanced braces")


def _top_block(t: str, key: str) -> tuple[int, int]:
    s = t.index("\n" + key + "={") + 1
    return s, _block_end(t, t.index("{", s))


def _node_order(t: str) -> list[str]:
    s, e = _top_block(t, "trade")
    return re.findall(r"\n\tnode=\{\n\t\tdefinitions=\"(\w+)\"", t[s:e])


def _node_span(t: str, node: str) -> tuple[int, int]:
    s, e = _top_block(t, "trade")
    m = re.search(r"\n\tnode=\{\n\t\tdefinitions=\"" + re.escape(node) + r"\"", t[s:e])
    if not m:
        raise PatchError(f"trade node {node!r} not in save")
    ns = s + m.start() + 1
    return ns, _block_end(t, t.index("{", ns))


def _entry_span(t: str, node: str, tag: str) -> tuple[int, int] | None:
    ns, ne = _node_span(t, node)
    m = re.search(r"\n\t\t" + tag + r"=\{", t[ns:ne])
    if not m:
        return None
    s = ns + m.start() + 1
    return s, _block_end(t, t.index("{", s))


def _country_span(t: str, tag: str) -> tuple[int, int]:
    s, e = _top_block(t, "countries")
    m = re.search(r"\n\t" + tag + r"=\{", t[s:e])
    if not m:
        raise PatchError(f"country {tag!r} not in save")
    cs = s + m.start() + 1
    return cs, _block_end(t, t.index("{", cs))


def _set_field(entry: str, key: str, value: str | None, indent: str = "\t\t\t") -> str:
    """set/replace/remove `key=value` among the direct fields of an entry block (one field per line)."""
    pat = re.compile(r"\n" + indent + re.escape(key) + r"=[^\n]*")
    if value is None:
        return pat.sub("", entry, count=1)
    if pat.search(entry):
        return pat.sub(f"\n{indent}{key}={value}", entry, count=1)
    close = entry.rstrip().rfind("\n")  # start of the block's closing line
    return f"{entry[:close]}\n{indent}{key}={value}{entry[close:]}"


def _outgoing(node: str) -> list[str]:
    g = json.loads(GRAPH.read_text())["nodes"]
    if node not in g:
        raise PatchError(f"unknown trade node {node!r}")
    return [o["target"] for o in g[node]["outgoing"]]  # same order as common/tradenodes/00_tradenodes.txt (checked)


# ------------------------------------------------------------------ merchants
def _steering_count(t: str, tag: str) -> int:
    s, e = _top_block(t, "trade")
    n = 0
    for m in re.finditer(r"\n\t\t" + tag + r"=\{", t[s:e]):
        b = t[s + m.start(): _block_end(t, t.index("{", s + m.start()))]
        if "has_trader=yes" in b and re.search(r"\n\t\t\ttype=1\b", b):
            n += 1
    return n


def _set_envoy_action(t: str, tag: str, busy: bool) -> str:
    """merchants={ envoy={ action=2 ... } }: action=2 on a stationed merchant (evidence: count of action=2 envoys ==
    count of has_trader entries in 663/663 countries, U25). Envoys carry no node; any free/busy one is used."""
    cs, ce = _country_span(t, tag)
    c = t[cs:ce]
    mi = c.find("\n\t\tmerchants={")
    if mi < 0:
        raise PatchError(f"{tag} has no merchants block")
    ms, me = mi + 1, _block_end(c, c.index("{", mi + 1))
    mb = c[ms:me]
    for em in re.finditer(r"\n\t\t\tenvoy=\{(.*?)\n\t\t\t\}", mb, re.S):
        has = "\n\t\t\t\taction=2" in em.group(1)
        if busy and not has:
            new = em.group(0).replace("\n\t\t\tenvoy={", "\n\t\t\tenvoy={\n\t\t\t\taction=2", 1)
        elif not busy and has:
            new = em.group(0).replace("\n\t\t\t\taction=2", "", 1)
        else:
            continue
        mb = mb[: em.start()] + new + mb[em.end():]
        c = c[:ms] + mb + c[me:]
        return t[:cs] + c + t[ce:]
    raise PatchError(f"{tag}: no {'free' if busy else 'stationed'} merchant")


def _set_transfer_home_bonus(t: str, tag: str) -> str:
    """country transfer_home_bonus = 0.1 x steering merchants (U25 0.300 with 3, U27 0.000 with 0, U28 0.100 with 1;
    R09). Only rewritten if the field exists."""
    cs, ce = _country_span(t, tag)
    c = t[cs:ce]
    v = f"{0.1 * _steering_count(t, tag):.3f}"
    c2 = re.sub(r"\n\t\ttransfer_home_bonus=[^\n]*", f"\n\t\ttransfer_home_bonus={v}", c, count=1)
    return t[:cs] + c2 + t[ce:]


def place_merchant(t: str, tag: str, node: str, role: str, direction: str | None = None) -> str:
    """Node entry: has_trader=yes; steer: type=1 and steer_power=<0-based index of `direction` in the node's outgoing
    list>, written only when > 0 (U25: ragusa->venice = 1, alexandria->venice = 1, wien->venice = 0 has no key);
    collect: no type/steer_power (516 collecting has_trader entries in U25 have neither).
    Country: one free envoy gets action=2; transfer_home_bonus recomputed."""
    if role not in ("collect", "steer"):
        raise PatchError("role must be 'collect' or 'steer'")
    span = _entry_span(t, node, tag)
    if span is None:
        # GUESS: a country without an entry in the node gets a minimal one at the end of the node block
        ns, ne = _node_span(t, node)
        close = t.rfind("\n\t}", ns, ne)
        t = t[:close] + "\n\t\t" + tag + "={\n\t\t}" + t[close:]
        span = _entry_span(t, node, tag)
    s, e = span
    entry = t[s:e]
    if "has_trader=yes" in entry:
        raise PatchError(f"{tag} already has a merchant in {node}")
    if role == "steer":
        outs = _outgoing(node)
        if direction not in outs:
            raise PatchError(f"{node} does not lead to {direction!r}; outgoing: {outs}")
        idx = outs.index(direction)
        entry = _set_field(entry, "type", "1")
        entry = _set_field(entry, "steer_power", str(idx) if idx else None)
    else:
        entry = _set_field(entry, "type", None)
        entry = _set_field(entry, "steer_power", None)
    entry = _set_field(entry, "has_trader", "yes")
    t = t[:s] + entry + t[e:]
    t = _set_envoy_action(t, tag, busy=True)
    return _set_transfer_home_bonus(t, tag)


def recall_merchant(t: str, tag: str, node: str) -> str:
    """Remove has_trader and type from the entry (U25 -> U27 ragusa: both gone, steer_power kept, no modifier added for
    the player's own recall). Country: one stationed envoy loses action=2; transfer_home_bonus recomputed."""
    span = _entry_span(t, node, tag)
    if span is None or "has_trader=yes" not in t[span[0]:span[1]]:
        raise PatchError(f"{tag} has no merchant in {node}")
    s, e = span
    entry = _set_field(_set_field(t[s:e], "has_trader", None), "type", None)
    t = t[:s] + entry + t[e:]
    t = _set_envoy_action(t, tag, busy=False)
    return _set_transfer_home_bonus(t, tag)


# ------------------------------------------------------------------ light ships
def set_light_ship_mission(t: str, tag: str, node: str, navy_id: int | None = None) -> str:
    """Put one of the tag's fleets on a protect-trade mission in `node` (evidence U25, VEN 2nd fleet, 3 barques):

        navy={ ... location=<sea zone> ... mission={ protect_mission={ retreat_port=.. was_safe_retreat_port=yes
               node=<1-based index of the node in the save's trade node list> trade=<sea zone>... current_route_target=..
               current_cycle_begin=.. on_my_way=no } } movement_locked=yes ... }

    Node entry light_ship=<n> equals the light ships of the tag's fleets on missions in that node (226/227 pairs, U25);
    ship_power and num_ships_protecting_trade are left to the game.
    GUESS (untested): the patrol route (trade= list) and location are copied from another fleet already protecting the
    same node in this save; retreat_port is kept from the fleet's own mission if it has one, else copied too; path and
    movement_progress are removed (teleport). Fails if no fleet in the save protects that node."""
    order = _node_order(t)
    if node not in order:
        raise PatchError(f"trade node {node!r} not in save")
    k = order.index(node) + 1
    # template mission for this node from any country
    tmpl = None
    s0, e0 = _top_block(t, "countries")
    for m in re.finditer(r"\n\t\t\t\tprotect_mission=\{(.*?)\n\t\t\t\t\}", t[s0:e0], re.S):
        if re.search(r"\n\t\t\t\t\tnode=" + str(k) + r"\n", m.group(1) + "\n"):
            tmpl = m.group(1)
            break
    if tmpl is None:
        raise PatchError(f"no fleet protects {node} in this save; no patrol route to copy")
    route = re.findall(r"\n\t\t\t\t\ttrade=(\d+)", tmpl)
    retreat = re.search(r"\n\t\t\t\t\tretreat_port=(\d+)", tmpl)
    cs, ce = _country_span(t, tag)
    c = t[cs:ce]
    chosen = None
    for nv in re.finditer(r"\n\t\tnavy=\{", c):
        ns = nv.start() + 1
        nb = c[ns:_block_end(c, c.index("{", ns))]
        nid = re.search(r"\n\t\t\tid=\{\n\t\t\t\tid=(\d+)", nb)
        types = re.findall(r'\n\t\t\t\ttype="(\w+)"', nb)
        if navy_id is not None:
            if nid and int(nid.group(1)) == navy_id:
                chosen = (ns, ns + len(nb), nb)
                break
        elif types and all(x in LIGHT_SHIP_TYPES for x in types):
            chosen = (ns, ns + len(nb), nb)
            break
    if chosen is None:
        raise PatchError(f"{tag}: no {'navy ' + str(navy_id) if navy_id else 'light-ship-only navy'} found")
    ns, ne, nb = chosen
    own_retreat = re.search(r"retreat_port=(\d+)", nb)
    rp = own_retreat.group(1) if own_retreat else (retreat.group(1) if retreat else None)
    mission = "\n\t\t\tmission={\n\t\t\t\tprotect_mission={\n"
    if rp:
        mission += f"\t\t\t\t\tretreat_port={rp}\n\t\t\t\t\twas_safe_retreat_port=yes\n"
    mission += f"\t\t\t\t\tnode={k}\n" + "".join(f"\t\t\t\t\ttrade={p}\n" for p in route)
    mission += "\t\t\t\t\tcurrent_route_target=0\n\t\t\t\t\tcurrent_cycle_begin=0\n\t\t\t\t\ton_my_way=no\n\t\t\t\t}\n\t\t\t}"
    nb2 = re.sub(r"\n\t\t\tmission=\{.*?\n\t\t\t\}", "", nb, count=1, flags=re.S)
    nb2 = re.sub(r"\n\t\t\tpath=\{[^}]*\}", "", nb2, count=1)
    nb2 = re.sub(r"\n\t\t\tmovement_progress=[^\n]*", "", nb2, count=1)
    if route:
        nb2 = re.sub(r"\n\t\t\tlocation=\d+", f"\n\t\t\tlocation={route[0]}", nb2, count=1)
    if "movement_locked=yes" not in nb2:
        mission += "\n\t\t\tmovement_locked=yes"
    close = nb2.rstrip().rfind("\n")  # start of the navy's closing line
    nb2 = nb2[:close] + mission + nb2[close:]
    c = c[:ns] + nb2 + c[ne:]
    return t[:cs] + c + t[ce:]


# ------------------------------------------------------------------ CLI
def main(argv: list[str]) -> None:
    if len(argv) < 4:
        sys.exit(__doc__)
    src, dst, op, *rest = argv
    t = Path(src).read_text(encoding="latin-1")
    if not t.startswith("EU4txt"):
        sys.exit("not a plain-text save (Ironman/compressed saves are not supported)")
    if op == "place":
        t = place_merchant(t, rest[0], rest[1], rest[2], rest[3] if len(rest) > 3 else None)
    elif op == "recall":
        t = recall_merchant(t, rest[0], rest[1])
    elif op == "ships":
        nid = int(rest[rest.index("--navy-id") + 1]) if "--navy-id" in rest else None
        t = set_light_ship_mission(t, rest[0], rest[1], nid)
    else:
        sys.exit(f"unknown op {op!r}")
    Path(dst).write_text(t, encoding="latin-1", newline="")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1:])
