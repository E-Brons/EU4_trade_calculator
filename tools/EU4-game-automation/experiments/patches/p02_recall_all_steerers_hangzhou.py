"""R08 Q5: node without steerers. Recall every steering merchant (has_trader + type=1) at hangzhou (3 links; only MNG
steers there on 1444.12.01), any country."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # tools/EU4-game-automation
import savepatch as sp  # noqa: E402

NODE = "hangzhou"


def patch(t: str) -> str:
    s, e = sp._node_span(t, NODE)
    tags = [m.group(1) for m in re.finditer(r"\n\t\t([A-Z0-9]{3})=\{", t[s:e])]
    recalled = []
    for tag in tags:
        span = sp._entry_span(t, NODE, tag)
        body = t[span[0]:span[1]]
        if "has_trader=yes" in body and re.search(r"\n\t\t\ttype=1\b", body):
            t = sp.recall_merchant(t, tag, NODE)
            recalled.append(tag)
    if not recalled:
        raise sp.PatchError(f"no steering merchant at {NODE}")
    print("recalled at", NODE, recalled, flush=True)
    return t
