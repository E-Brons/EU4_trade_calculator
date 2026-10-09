"""Reads a save file into text and finds blocks in it. No game logic.

A `.eu4` is a zip (gamestate/meta/ai), a plain-text file (non-Ironman bookmark saves) or an already-melted flat text file.
Binary Ironman saves are melted through app.parsing.ironman_melt (pdx.tools).
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

from app.parsing import ironman_melt


@dataclass(frozen=True)
class SaveText:
    meta: str
    gamestate: str
    ironman: bool


def read_save_text(path: str | Path) -> SaveText:
    p = Path(path)
    if zipfile.is_zipfile(p):
        with zipfile.ZipFile(p) as zf:
            names = set(zf.namelist())
            if "gamestate" not in names:
                raise ValueError(f"{p.name} doesn't look like an EU4 save (no 'gamestate' member)")
            gamestate_raw = zf.read("gamestate")
            meta_raw = zf.read("meta") if "meta" in names else gamestate_raw
        if ironman_melt.is_binary(gamestate_raw):
            melted = ironman_melt.melt_ironman_save(p.read_bytes())
            text = ironman_melt.ensure_text(melted).decode("utf-8", errors="replace")
            return SaveText(meta=text, gamestate=text, ironman=True)
        return SaveText(
            meta=ironman_melt.ensure_text(meta_raw).decode("utf-8", errors="replace"),
            gamestate=ironman_melt.ensure_text(gamestate_raw).decode("utf-8", errors="replace"),
            ironman=False,
        )
    text = p.read_text(encoding="utf-8", errors="replace")
    return SaveText(meta=text, gamestate=text, ironman=False)


def extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf'(?m)^\s*{re.escape(key)}\s*=\s*"?([^"\n]+?)"?\s*$', text)
    return match.group(1) if match else None


_COUNTRY_START = re.compile(r"\n\t([A-Z0-9]{3})=\{")


def country_spans(gamestate: str) -> dict[str, tuple[int, int]]:
    """tag -> (start, end) of every block under the top-level `countries`, found by the save's tab indentation (the game
    and the Ironman melter write one tab per level), so the 50+ MB document is never tokenized. Empty if not found."""
    start = gamestate.find("\ncountries={")
    if start < 0:
        return {}
    end = gamestate.find("\n}", start + 1)
    spans: dict[str, tuple[int, int]] = {}
    pos = start
    while (m := _COUNTRY_START.search(gamestate, pos, end)) is not None:
        close = gamestate.find("\n\t}", m.end())
        spans[m.group(1)] = (m.end(), close)
        pos = close
    return spans


def block_fields(text: str, span: tuple[int, int], keys: tuple[str, ...], indent: str = "\t\t") -> str:
    """The `key=value` / `key={...}` lines of `keys` directly inside a tab-indented block, joined (every occurrence)."""
    body = text[span[0]:span[1]]
    parts: list[str] = []
    for m in re.finditer(rf"\n{indent}({'|'.join(map(re.escape, keys))})=", body):
        j = m.end()
        if body.startswith("{", j):
            close = body.find(f"\n{indent}}}", j)
            parts.append(f"{m.group(1)}={body[j:close + len(indent) + 2]}")
        else:
            parts.append(f"{m.group(1)}={body[j:body.find(chr(10), j)]}")
    return "\n".join(parts)


def extract_top_level_block(text: str, key: str) -> str | None:
    """`key={ ... }` at brace depth 0, including its braces, without tokenizing the rest of a huge document."""
    i, n, depth, in_quotes = 0, len(text), 0, False
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
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 0:
            brace = _key_eq_brace_at(text, i, key)
            if brace is not None:
                end = _match_brace_block(text, brace)
                if end is not None:
                    return text[brace:end]
        i += 1
    return None


def extract_nested_block(text: str, outer_key: str, inner_key: str) -> str | None:
    """`outer_key={ inner_key={...} ... }`, stopping the moment `inner_key` is found at depth 1."""
    outer = extract_top_level_start(text, outer_key)
    if outer is None:
        return None
    n, depth, in_quotes, i = len(text), 0, False, outer
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
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return None
        elif depth == 1:
            brace = _key_eq_brace_at(text, i, inner_key)
            if brace is not None:
                end = _match_brace_block(text, brace)
                return text[brace:end] if end is not None else None
        i += 1
    return None


def extract_top_level_start(text: str, key: str) -> int | None:
    i, n, depth, in_quotes = 0, len(text), 0, False
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
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 0:
            brace = _key_eq_brace_at(text, i, key)
            if brace is not None:
                return brace
        i += 1
    return None


def _key_eq_brace_at(text: str, i: int, key: str) -> int | None:
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
    n, depth, in_quotes, k = len(text), 0, False, start
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
