"""Step 1: every output save has date= matching its file name, player=VEN, EU4txt."""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); from common import OUT
bad = 0; n = 0
for f in sorted(OUT.glob("*/*.eu4")):
    head = f.open("rb").read(3000).decode("latin-1"); n += 1
    m = re.search(r"_(\d{4})\.(\d\d)\.(\d\d)\.eu4$", f.name)
    want = f"{int(m[1])}.{int(m[2])}.{int(m[3])}" if m else None
    date = re.search(r"\ndate=([\d.]+)", head); pl = re.search(r'\nplayer="(\w*)"', head)
    probs = []
    if not head.startswith("EU4txt"): probs.append("not EU4txt")
    if not date or date[1] != want: probs.append(f"date {date and date[1]} != {want}")
    if not pl or pl[1] != "VEN": probs.append(f"player {pl and pl[1]}")
    if probs: bad += 1; print("PROBLEM", f.relative_to(OUT), probs)
print(f"{n} saves checked, {bad} with problems")
