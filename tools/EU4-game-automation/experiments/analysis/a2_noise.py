"""Step 2: noise between runs. Trade block flattened field diff + whole-file line diff (diff -U0)."""
import subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import block, flat, save, OUT

def trade_diff(a, b):
    fa, fb = flat(block(a, "trade")), flat(block(b, "trade"))
    keys = set(fa) | set(fb)
    d = [k for k in keys if fa.get(k) != fb.get(k)]
    return len(keys), d

def line_diff(a, b):
    r = subprocess.run(["diff", "-U0", str(a), str(b)], capture_output=True, text=True, errors="replace")
    return sum(1 for l in r.stdout.splitlines() if l[:1] in "+-" and l[:3] not in ("+++", "---"))

pairs = [("E01a", "E01b"), ("E01a", "E01c"), ("E01a", "E01d"), ("E00", "E01a")]
for x, y in pairs:
    for w in ("t1", "t2"):
        a, b = save(x, w), save(y, w)
        n, d = trade_diff(a, b)
        print(f"{x} vs {y} {w}: trade fields {len(d)}/{n} differ; file lines differing {line_diff(a, b)}")
        if d: print("   e.g.", sorted(d)[:6])
