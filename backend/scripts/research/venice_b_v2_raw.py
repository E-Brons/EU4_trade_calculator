"""SECOND PASS (independent of clausewitz.parse and of the venice_b_* analysis code): raw-text regex extraction, used by the checks below."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.trade import savefile

SAVES = Path(__file__).resolve().parents[2] / 'tests' / 'fixtures' / 'saves'
ENTRY = re.compile(r'\b([A-Z][A-Z0-9]{2})=\{((?:[^{}]|\{[^{}]*\})*)\}')
KV = re.compile(r'(\w+)=("[^"]*"|[^\s{}]+)')

def files():
    fs = sorted(SAVES.glob('Venice*.eu4'), key=lambda p: tuple(int(x) for x in p.stem[6:].split('_')))
    return fs

_cache = {}
def text(p):
    if p not in _cache:
        _cache.clear(); _cache[p] = p.read_text(encoding='utf-8', errors='replace')
    return _cache[p]

def tradeblock(p):
    return savefile.extract_top_level_block(text(p), 'trade')

def nodes(p):
    tb = tradeblock(p)
    idx = [m.start() for m in re.finditer(r'definitions="', tb)]
    out = {}
    for i, s in enumerate(idx):
        seg = tb[s: idx[i + 1] if i + 1 < len(idx) else len(tb)]
        name = re.match(r'definitions="([^"]+)"', seg).group(1)
        ents = {}
        for m in ENTRY.finditer(seg):
            d = {k: v for k, v in KV.findall(m.group(2))}
            ents[m.group(1)] = d
        wl = re.findall(r'\n\t\tsteer_power=([\d.]+)', seg)
        out[name] = (ents, seg, '{' + ' '.join(wl) + '}' if wl else None)
    return out

def country_block(p, tag):
    return savefile.extract_nested_block(text(p), 'countries', tag)
