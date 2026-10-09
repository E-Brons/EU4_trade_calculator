"""Second-pass checks for the Venice timing claims; different code paths from venice_a_*.py (text diff of the raw trade block; own prev loop with Decimal; own R loop)."""
import re, sys, json, collections
from decimal import Decimal as Dc, ROUND_DOWN
from pathlib import Path
sys.path.insert(0, "scripts/research")
import venice_load as V
from app.trade import savefile

G = json.load(open("data/tradenodes.json"))["nodes"]
LINKS = {n: [o["target"] for o in v["outgoing"]] for n, v in G.items()}
FS = V.files()

def tradetext(p):
    return savefile.extract_top_level_block(p.read_text(encoding="utf-8", errors="replace"), "trade")

def claim1():
    """changed lines of the raw trade block between consecutive saves, by key name"""
    prev = None
    for p in FS:
        lines = tradetext(p).split("\n")
        if prev:
            a, b = prev[1], lines
            ca = collections.Counter(a); cb = collections.Counter(b)
            diff = (ca - cb) + (cb - ca)
            keys = collections.Counter(re.match(r"\s*([A-Za-z_0-9]+)", l).group(1) for l in diff.elements() if re.match(r"\s*([A-Za-z_0-9]+)", l))
            print(prev[0], "->", p.stem[6:], "changed lines", sum(diff.values()), dict(keys.most_common(8)))
        prev = (p.stem[6:], lines)

def claim2():
    """gate with the first save's weights, own loop with Decimal; ticks only"""
    def read(p):
        tree = V.load(p, "trade"); nodes = [n for n in (tree["node"] if isinstance(tree["node"], list) else [tree["node"]]) if isinstance(n, dict) and n.get("definitions")]
        return {n["definitions"]: n for n in nodes}
    w0 = {k: [Dc(str(x)) for x in (n["steer_power"] if isinstance(n.get("steer_power"), list) else [n.get("steer_power", 0)])] for k, n in read(FS[0]).items()}
    for p in FS:
        if not p.stem[6:].endswith(("_01", "1445_07_02")) or p.stem[6:] in ("1444_11_11",) or p.stem[6:].split("_")[2] not in ("01", "02") or p.stem[6:] in ("1445_01_02",): continue
        N = read(p); total = ok = 0
        for B, n in N.items():
            for tag, e in n.items():
                if not (isinstance(e, dict) and "max_pow" in e): continue
                total += 1; s = Dc(0)
                for i, D in enumerate(LINKS.get(B, [])):
                    d = N[D].get(tag)
                    if isinstance(d, dict) and Dc(str(d.get("province_power", 0))) >= 10 and i < len(w0[B]) and w0[B][i] > 0:
                        s += (Dc(str(d["province_power"])) / 5).quantize(Dc("0.001"), rounding=ROUND_DOWN)
                ok += abs(s - Dc(str(e.get("prev", 0)))) < Dc("0.0005")
        print(p.stem[6:], "entries", total, "exact with bookmark-start weight gate", ok)

if __name__ == "__main__":
    {"1": claim1, "2": claim2}[sys.argv[1]]()
