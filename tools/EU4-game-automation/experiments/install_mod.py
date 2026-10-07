#!/usr/bin/env python3
"""Install the experiments mod into the EU4 user folder (copy + .mod descriptor). Jobs enable it with
"mods": ["mod/eu4_experiments.mod"]; the runner writes dlc_load.json per job and restores it afterwards.

    python3 tools/EU4-game-automation/experiments/install_mod.py           # install / update
    python3 tools/EU4-game-automation/experiments/install_mod.py remove
"""
import shutil
import sys
from pathlib import Path

USER = Path.home() / "Documents/Paradox Interactive/Europa Universalis IV"
SRC = Path(__file__).resolve().parent / "mod" / "eu4_experiments"
NAME = "eu4_experiments"


def install() -> None:
    dst = USER / "mod" / NAME
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst, ignore=shutil.ignore_patterns("descriptor.mod"))
    desc = (SRC / "descriptor.mod").read_text()
    (USER / "mod" / f"{NAME}.mod").write_text(desc + f'path="mod/{NAME}"\n', encoding="utf-8")
    print("installed", dst)


def remove() -> None:
    shutil.rmtree(USER / "mod" / NAME, ignore_errors=True)
    (USER / "mod" / f"{NAME}.mod").unlink(missing_ok=True)
    print("removed")


if __name__ == "__main__":
    remove() if sys.argv[1:] == ["remove"] else install()
