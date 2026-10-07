#!/usr/bin/env python3
"""Install / remove the spike mod and switch the enabled-mod list.  usage: install.py install | restore | status

install : copies spike/mod to <userdir>/mod/eu4_automation_spike, writes its .mod file, backs up dlc_load.json
          (once) and enables ONLY the spike mod, so the user's other mods cannot influence the test.
restore : puts the original dlc_load.json back and removes the spike mod.
"""
import json, shutil, sys
from pathlib import Path

USER = Path.home() / "Documents/Paradox Interactive/Europa Universalis IV"
SRC = Path(__file__).parent / "mod"
NAME = "eu4_automation_spike"
DLC = USER / "dlc_load.json"
BAK = USER / "dlc_load.json.automation_backup"


def install():
    dst = USER / "mod" / NAME
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst, ignore=shutil.ignore_patterns("descriptor.mod"))
    (USER / "mod" / f"{NAME}.mod").write_text(
        f'name="EU4 Automation Spike"\npath="mod/{NAME}"\nsupported_version="1.37.*.*"\n', encoding="utf-8")
    if not BAK.exists():
        shutil.copy2(DLC, BAK)
    cfg = json.loads(BAK.read_text())
    cfg["enabled_mods"] = [f"mod/{NAME}.mod"]
    DLC.write_text(json.dumps(cfg), encoding="utf-8")
    print("installed; enabled_mods =", cfg["enabled_mods"], "| backup:", BAK)


def restore():
    if BAK.exists():
        shutil.copy2(BAK, DLC)
        BAK.unlink()
    shutil.rmtree(USER / "mod" / NAME, ignore_errors=True)
    (USER / "mod" / f"{NAME}.mod").unlink(missing_ok=True)
    print("restored:", DLC.read_text())


def status():
    print("dlc_load.json:", DLC.read_text())
    print("backup present:", BAK.exists(), "| mod installed:", (USER / "mod" / NAME).exists())


if __name__ == "__main__":
    {"install": install, "restore": restore, "status": status}[sys.argv[1] if len(sys.argv) > 1 else "status"]()
