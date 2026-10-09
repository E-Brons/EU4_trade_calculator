"""Independent (regex, no clausewitz parser, no cache) readers for the second-pass checks of fork C.

trade_entries(text) -> ({(node, tag): {key: value}}, {node: {key: value}}), country_segment(text, tag).
"""
from __future__ import annotations
import re
from pathlib import Path

SAVES = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "saves"
_ENTRY = re.compile(r"\n\t\t([A-Z][A-Z0-9]{2})=\{\n(.*?)\n\t\t\}", re.S)
_KV = re.compile(r"\t\t\t([a-z_]+)=([^\n{]*)\n")


def read(name: str) -> str:
    return (SAVES / name).read_text(encoding="latin-1")


def _num(v: str):
    v = v.strip().strip('"')
    if v in ("yes", "no"):
        return v == "yes"
    try:
        return float(v)
    except ValueError:
        return v


def trade_block(text: str) -> str:
    i = text.index("\ntrade={\n")
    j = text.index("\n}\n", i)
    return text[i:j]


def trade_entries(text: str):
    out, nodes = {}, {}
    blk = trade_block(text)
    parts = blk.split("\n\tnode={\n")[1:]
    for part in parts:
        name = re.search(r'definitions="([^"]+)"', part).group(1)
        head = part.split("\n\t\tPIR={")[0]
        nodes[name] = {m.group(1): _num(m.group(2)) for m in re.finditer(r"\n\t\t([a-z_]+)=([^\n{]*)(?=\n)", "\n" + head)}
        for m in _ENTRY.finditer(part):
            out[(name, m.group(1))] = {k: _num(v) for k, v in _KV.findall(m.group(2) + "\n")}
    return out, nodes


def country_segment(text: str, tag: str) -> str:
    i = text.index("\ncountries={\n")
    m = re.compile(rf"\n\t{tag}=\{{\n").search(text, i)
    n = re.compile(r"\n\t[A-Z][A-Z0-9]{2}=\{\n").search(text, m.end())
    return text[m.start(): n.start() if n else len(text)]


def scalar(seg: str, key: str):
    m = re.search(rf"\n\t\t{key}=([^\n{{]*)\n", seg)
    return _num(m.group(1)) if m else None


def _balanced(text: str, start: int) -> str:
    depth = 0
    for j in range(start, len(text)):
        c = text[j]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return text[start: j + 1]
    return text[start:]


def ruler_dip(seg: str):
    """DIP of the history `monarch={...}` block whose id equals the country's current `monarch={ id={ id=N` (None if not found)."""
    cur = re.search(r"\n\t\tmonarch=\{\n\t\t\tid=(\d+)", seg)
    hs = seg.find("\n\t\thistory={")
    if hs < 0 or not cur:
        return None
    hist = _balanced(seg, seg.index("{", hs))
    for m in re.finditer(r"\n\t\t\t(?:\t)*monarch=\{", hist):
        blk = _balanced(hist, m.end() - 1)
        mid = re.search(r"id=\{\n\t*id=(\d+)", blk)
        d = re.search(r"\n\t*DIP=(\d+)", blk)
        if mid and d and mid.group(1) == cur.group(1):
            return int(d.group(1))
    return None
