"""Parser for Paradox's "Clausewitz" text format used by EU4 game files and
melted save files.

The format looks like::

    key = "value"
    nested = {
        a = 1
        b = { 1 2 3 }
    }
    repeated = { name="x" }
    repeated = { name="y" }

Grammar notes handled here:
- Whitespace-separated tokens; `=` is optional between a key and a `{`
  (some save fields omit it, e.g. `color = rgb { 1 2 3 }` variants) but we
  only need to support the standard `key=value` / `key={...}` forms that
  appear in tradenodes files and melted saves.
- Values are either a scalar (bareword, quoted string, number, date) or a
  block `{ ... }`.
- A block is either:
    * a list of scalars, e.g. `{ 1 2 3 }` -> Python list
    * a list of key=value pairs, e.g. `{ a=1 b=2 }` -> Python dict
  A block is treated as a dict if any top-level item inside it is a
  `key=value` pair; otherwise it's a list of scalar values.
- Duplicate keys at the same level (e.g. multiple `outgoing={...}`) are
  collapsed into a list under that key, in first-seen order.
- Comments start with `#` and run to end of line.
"""
from __future__ import annotations

import re
from typing import Any

_TOKEN_RE = re.compile(
    r"""
    \#[^\n]*                      # comment
    | "(?:[^"\\]|\\.)*"           # quoted string
    | [={}]                       # structural tokens
    | [^\s={}"]+                  # bareword / number / date
    """,
    re.VERBOSE,
)


def tokenize(text: str) -> list[str]:
    tokens = []
    for match in _TOKEN_RE.finditer(text):
        tok = match.group(0)
        if tok.startswith("#"):
            continue
        tokens.append(tok)
    return tokens


def _unquote(tok: str) -> str:
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return tok[1:-1].replace('\\"', '"')
    return tok


def _coerce_scalar(tok: str) -> Any:
    if len(tok) >= 2 and tok[0] == '"' and tok[-1] == '"':
        return _unquote(tok)
    if re.fullmatch(r"-?\d+", tok):
        try:
            return int(tok)
        except ValueError:
            return tok
    if re.fullmatch(r"-?\d+\.\d+", tok):
        try:
            return float(tok)
        except ValueError:
            return tok
    if tok == "yes":
        return True
    if tok == "no":
        return False
    return tok


class _Parser:
    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> str:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def parse_document(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        while self.peek() is not None:
            self._parse_assignment_into(result)
        return result

    def _parse_assignment_into(self, result: dict[str, Any]) -> None:
        key_tok = self.next()
        key = _unquote(key_tok)
        if self.peek() == "=":
            self.next()
        value = self._parse_value()
        _assign(result, key, value)

    def _parse_value(self) -> Any:
        tok = self.peek()
        if tok == "{":
            return self._parse_block()
        return _coerce_scalar(self.next())

    def _parse_block(self) -> Any:
        assert self.next() == "{"
        # Empty block -> empty dict
        if self.peek() == "}":
            self.next()
            return {}

        # Decide dict-vs-list by lookahead: if the token after the first
        # token is "=", this block is a dict of key=value pairs.
        is_dict = self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1] == "="

        if is_dict:
            result: dict[str, Any] = {}
            while self.peek() != "}":
                if self.peek() is None:
                    raise ValueError("Unexpected end of input inside block")
                self._parse_assignment_into(result)
            self.next()  # consume "}"
            return result
        else:
            items = []
            while self.peek() != "}":
                if self.peek() is None:
                    raise ValueError("Unexpected end of input inside block")
                items.append(self._parse_value())
            self.next()  # consume "}"
            return items


def _assign(result: dict[str, Any], key: str, value: Any) -> None:
    if key in result:
        existing = result[key]
        if isinstance(existing, list) and result.get(f"__list__{key}", False):
            existing.append(value)
        else:
            result[key] = [existing, value]
            result[f"__list__{key}"] = True
    else:
        result[key] = value


def parse(text: str) -> dict[str, Any]:
    """Parse a Clausewitz-format text document into a nested dict/list tree.

    Duplicate keys become lists (in first-seen order). Marker keys of the
    form ``__list__<key>`` are internal bookkeeping and are stripped from
    the output.
    """
    tokens = tokenize(text)
    tree = _Parser(tokens).parse_document()
    return _strip_markers(tree)


def _strip_markers(node: Any) -> Any:
    if isinstance(node, dict):
        return {
            k: _strip_markers(v)
            for k, v in node.items()
            if not k.startswith("__list__")
        }
    if isinstance(node, list):
        return [_strip_markers(v) for v in node]
    return node


def as_list(value: Any) -> list:
    """Normalize a parsed value that may be a single dict/scalar or a list
    of them (due to duplicate keys) into always a list."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
