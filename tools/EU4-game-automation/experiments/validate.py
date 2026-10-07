#!/usr/bin/env python3
"""Validate the generated experiments offline (no game):
  1. every job JSON parses; every referenced file exists (the base save is produced by E00 and may be missing);
  2. every effect keyword used in effects/*.txt appears as an effect in the game's own scripts; every exp_* modifier
     used exists in the experiments mod;
  3. countries/provinces named in the effects exist with the expected owner in a 1444.12.01 save (U10 of the Venice
     series, the same bookmark state the base save E00 has) ;
  4. every patch module runs on that save (patches that refuse are reported, not hidden).

    python3 tools/EU4-game-automation/experiments/validate.py [path/to/1444.12.01.eu4]
"""
import importlib.util
import io
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
GAME = Path.home() / "Library/Application Support/Steam/steamapps/common/Europa Universalis IV"
U10 = REPO / "datasets/eu4/1.37.5/vanilla/dlc-819b35e6/venice-1444/U10_VEN.1444.12.01.eu4.zip"
ok = True


def fail(msg: str) -> None:
    global ok
    ok = False
    print("FAIL", msg)


def game_effect_names() -> set[str]:
    names: set[str] = set()
    for d in ("events", "decisions", "missions", "common/scripted_effects"):
        for f in (GAME / d).rglob("*.txt"):
            names |= set(re.findall(r"(?m)^\s*([a-z_]+)\s*=", f.read_text(encoding="latin-1", errors="replace")))
    return names


def load_save(arg: str | None) -> str:
    if arg:
        return Path(arg).read_text(encoding="latin-1")
    with zipfile.ZipFile(U10) as z:
        return z.read(z.namelist()[0]).decode("latin-1")


def main() -> None:
    # 1. jobs and references
    for job in sorted((HERE / "jobs").glob("*.json")):
        spec = json.loads(job.read_text())
        for k in ("nation", "mods", "observe", "script"):
            if k not in spec:
                fail(f"{job.name}: missing {k}")
        refs = [spec["base_save"]] if spec.get("base_save") else []
        for st in spec["script"]:
            refs += [st[k] for k in ("console_commands", "effects", "patch") if st.get(k)]
            if "outfname" in st and "/out/" not in st["outfname"]:
                fail(f"{job.name}: outfname outside out/: {st['outfname']}")
        for r in refs:
            p = (job.parent / r).resolve()
            if not p.exists():
                (print if r.endswith("base_1444.12.01.eu4") else fail)(f"{'note' if r.endswith('.eu4') else ''} {job.name}: {r} missing" + (" (written by E00)" if r.endswith(".eu4") else ""))
    print("jobs:", len(list((HERE / "jobs").glob("*.json"))))

    # 2. effect keywords and modifiers
    known = game_effect_names()
    mods = set(re.findall(r"(?m)^(exp_\w+)\s*=", (HERE / "mod/eu4_experiments/common/event_modifiers/zz_exp_modifiers.txt").read_text()))
    structural = {"who", "duration", "power", "key", "name", "subject", "subject_type"}
    for f in sorted((HERE / "effects").glob("*.txt")):
        t = f.read_text()
        for kw in re.findall(r"(?m)^\s*([a-z_]+)\s*=", t):
            if kw not in known and kw not in structural:
                fail(f"{f.name}: effect {kw!r} not used anywhere in the game scripts")
        for m in re.findall(r"name = (exp_\w+)", t):
            if m not in mods:
                fail(f"{f.name}: modifier {m} not in the experiments mod")
    print("effect keywords checked against", len(known), "names in game scripts")

    # 3. countries / provinces in the bookmark-state save
    save = load_save(sys.argv[1] if len(sys.argv) > 1 else None)
    def owner(pid: int) -> str | None:
        m = re.search(r"\n-" + str(pid) + r"=\{\n(.*?)\n\t\}", save, re.S)
        o = re.search(r'\n\t\towner="(\w+)"', m.group(1)) if m else None
        return o.group(1) if o else None
    for pid, want in ((103, "SAV"), (112, "VEN"), (163, "VEN"), (4729, "VEN"), (164, "NAX"), (109, "MAN")):
        got = owner(pid)
        print(f"province {pid}: owner {got}" + ("" if got == want else f"  (expected {want})"))
        if got != want:
            fail(f"province {pid} owner {got}, expected {want}")

    # 4. patches
    sys.path.insert(0, str(HERE.parent))
    for p in sorted((HERE / "patches").glob("*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out = io.StringIO()
        try:
            old = sys.stdout
            sys.stdout = out
            res = mod.patch(save)
        except Exception as e:  # noqa: BLE001
            sys.stdout = old
            print(f"patch {p.name}: REFUSED/ERROR {type(e).__name__}: {e} {out.getvalue().strip()}")
            continue
        finally:
            sys.stdout = old
        from collections import Counter
        a, b = Counter(save.splitlines()), Counter(res.splitlines())
        changed = sum(((a - b) + (b - a)).values())
        print(f"patch {p.name}: ok, ~{changed} lines changed {out.getvalue().strip()}")
    print("OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
