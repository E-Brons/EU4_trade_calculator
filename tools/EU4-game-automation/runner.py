#!/usr/bin/env python3
"""EU4 job runner: plays one job spec through the worker (bridge.py) and writes the requested saves.

    python3 tools/EU4-game-automation/runner.py job.json

Spec (paths are relative to the job file):
{
  "nation": "VEN",                 # country the saves are written for (player=<nation> in every save)
  "start_date": "1444.11.11",      # only the default 1444.11.11 bookmark is supported for new games
  "base_save": null,               # or a .eu4 file to continue from instead of a new game
  "mods": [],                      # enabled_mods entries for dlc_load.json, e.g. "mod/x.mod"
  "observe": true,                 # spectator mode between steps: AI runs every country, no event pop-ups
  "script": [
    {"console_commands": "c.txt",  # optional: one console line per line, '#' comments
     "effects": "e.txt",           # optional: effect file run via `run` while tagged as <nation>
     "patch": "p.py",              # optional: module with patch(text) -> text, applied to a save that is then reloaded
     "date": "1444.12.01",         # optional: run until this date (console `stop` + `speed 5`), verified from a save
     "outfname": "out.eu4"}        # optional: write the save here
  ]
}
The worker must be running (python3 tools/EU4-game-automation/worker.py in an ordinary iTerm tab).
dlc_load.json and continue_game.json are backed up first and always restored.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bridge import BRIDGE, submit  # noqa: E402

EU4 = Path.home() / "Documents/Paradox Interactive/Europa Universalis IV"
SAVES = EU4 / "save games"

# click targets, 2048-px-wide game window at 1x (verified 2026-10-06, EU4 1.37.5, settings size 2048x1330)
SINGLE_PLAYER = (901, 1240)
CONTINUE_GAME = (980, 1148)
ACHIEVE_OK = (1149, 854)
NATION_VEN = (1003, 642)      # Venice on the default nation-select camera
NATION_PLAY = (1876, 1310)
MODE_PLAY = (1147, 924)
INTRO_CLOSE = (1024, 1132)


class JobError(RuntimeError):
    pass


def _date(s: str) -> dt.date:
    y, m, d = (int(x) for x in s.split("."))
    return dt.date(y, m, d)


def game_running() -> bool:
    return bool(submit("ping").get("game_pid"))


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class Runner:
    def __init__(self, spec: dict, base: Path, log=print):
        self.spec, self.base, self.log = spec, base, log
        self.nation = spec["nation"].upper()
        self.observe = bool(spec.get("observe", True))
        self.ai_off = [t.upper() for t in spec.get("ai_off", [])]  # tags whose AI is disabled while observing
        self.current: dt.date | None = None
        self.n_tmp = 0

    # ------------------------------------------------------------ helpers
    def path(self, p: str) -> Path:
        q = Path(p).expanduser()
        return q if q.is_absolute() else (self.base / q)

    def wait_screen(self, wanted: set[str], max_s: float = 120) -> str:
        end = time.time() + max_s
        last = None
        while time.time() < end:
            last = submit("screen")
            if last["screen"] in wanted:
                return last["screen"]
            time.sleep(2)
        raise JobError(f"expected screen {sorted(wanted)}, last seen {last}")

    def enter_observe(self) -> None:
        """Spectator mode. Leaving a tag hands it back to the AI with AI on, so `ai <tag>` (a toggle) is re-issued
        for every ai_off tag each time; otherwise the AI undoes patched merchants within a month."""
        self.console("observe", *[f"ai {t}" for t in self.ai_off])

    def console(self, *lines: str) -> None:
        if lines:
            submit("console", lines=list(lines), timeout=300)

    def save_to(self, name: str) -> dict:
        """Write a save as <nation> (tag in, save, back to observer) and return worker info incl. the save's date."""
        if self.observe:
            self.console(f"tag {self.nation}")
        info = submit("save", name=name, timeout=300)
        if self.observe:
            self.enter_observe()
        if info.get("format") != "EU4txt":
            raise JobError(f"save is not plain text: {info}")
        self.current = _date(info["date"])
        return info

    # ------------------------------------------------------------ start
    def point_continue(self, src: Path) -> None:
        """Copy src into save games/ and point continue_game.json at it. EU4 reads continue_game.json at launch,
        so this must happen before the game starts (writing it while the menu shows loads the previous save)."""
        dst = SAVES / "automation_load.eu4"
        shutil.copyfile(src, dst)  # fresh mtime: Continue Game picks the newest save file, not only the json entry
        os.utime(dst, None)
        cg = EU4 / "continue_game.json"
        d = json.loads(cg.read_text())
        d.update(title="Automation", filename="save games/automation_load.eu4")
        cg.write_text(json.dumps(d, indent="\t"))

    def start(self) -> None:
        if game_running():
            submit("quit", timeout=120)
        if self.spec.get("base_save"):
            self.point_continue(self.path(self.spec["base_save"]))
        submit("launch", timeout=200)
        self.wait_screen({"menu"}, 180)
        submit("fit_window")
        time.sleep(1)
        self.wait_screen({"menu"}, 30)
        base_save = self.spec.get("base_save")
        if base_save:
            self.load_save(self.path(base_save), already_in_menu=True)
        else:
            if self.spec.get("start_date", "1444.11.11") != "1444.11.11":
                raise JobError("start_date other than 1444.11.11 is not supported yet (use base_save)")
            submit("click", x=SINGLE_PLAYER[0], y=SINGLE_PLAYER[1])
            self.wait_screen({"select"}, 60)
            submit("click", x=NATION_VEN[0], y=NATION_VEN[1])
            time.sleep(1.5)
            submit("click", x=NATION_PLAY[0], y=NATION_PLAY[1])
            self.wait_screen({"mode"}, 60)
            submit("click", x=MODE_PLAY[0], y=MODE_PLAY[1])
            if self.wait_screen({"intro", "ingame"}, 240) == "intro":
                submit("click", x=INTRO_CLOSE[0], y=INTRO_CLOSE[1])
                time.sleep(1)
            self.wait_screen({"ingame"}, 30)
            self.current = _date("1444.11.11")
        self.console(f"tag {self.nation}")
        if self.observe:
            self.enter_observe()

    def load_save(self, src: Path, already_in_menu: bool = False) -> None:
        """Continue Game from `src` (copied into save games/ under an automation name)."""
        if not already_in_menu:
            self.point_continue(src)
            submit("quit", timeout=120)
            submit("launch", timeout=200)
            self.wait_screen({"menu"}, 180)
            submit("fit_window")
            time.sleep(1)
            self.wait_screen({"menu"}, 30)
        submit("click", x=CONTINUE_GAME[0], y=CONTINUE_GAME[1])
        if self.wait_screen({"achieve", "ingame"}, 240) == "achieve":
            submit("click", x=ACHIEVE_OK[0], y=ACHIEVE_OK[1])
            self.wait_screen({"ingame"}, 240)
        head = open(src, "rb").read(4096).decode("latin-1")
        m = re.search(r"\ndate=([\d.]+)", head)
        self.current = _date(m.group(1)) if m else None
        self.console(f"tag {self.nation}")
        expected = self.current
        self.n_tmp += 1
        info = submit("save", name=f"_runner_check_{self.n_tmp}", timeout=300)
        if _date(info["date"]) != expected:
            raise JobError(f"loaded the wrong save: game date {info['date']}, expected {expected} from {src.name}")
        if self.observe:
            self.enter_observe()

    # ------------------------------------------------------------ steps
    def run_to(self, target: dt.date) -> dict:
        tstr = f"{target.year}.{target.month:02d}.{target.day:02d}"
        for attempt in range(4):
            days = (target - self.current).days if self.current else 400
            if days < 0:
                raise JobError(f"step date {tstr} is before the game date {self.current}")
            if days == 1:  # verified 2026-10-07: `stop` for the next day is accepted but never fires (>= 2 days works)
                raise JobError(f"step to {tstr} is 1 day: EU4 `stop` ignores the next day; use steps of >= 2 days")
            if days > 0:
                self.console(f"stop {tstr}", "speed 5")
                time.sleep(2)
                submit("wait_stopped", max_s=90 + days * 1.0, timeout=150 + days * 1.5)
            self.n_tmp += 1
            info = self.save_to(f"_runner_check_{self.n_tmp}")
            if self.current == target:
                return info
            self.log(f"  stopped at {self.current}, target {tstr} (attempt {attempt + 1})")
        raise JobError(f"could not reach {tstr}; game date {self.current}")

    def run_step(self, i: int, step: dict) -> dict:
        res: dict = {"step": i}
        if step.get("console_commands"):
            lines = [ln.strip() for ln in self.path(step["console_commands"]).read_text().splitlines()]
            lines = [ln for ln in lines if ln and not ln.startswith("#")]
            self.log(f"  console: {lines}")
            self.console(*lines)
        if step.get("effects"):
            name = f"automation_effects_{i}.txt"
            shutil.copy2(self.path(step["effects"]), EU4 / name)
            self.log(f"  effects: {step['effects']}")
            self.console(f"tag {self.nation}", f"run {name}")
            if self.observe:
                self.enter_observe()
        if step.get("patch"):
            self.apply_patch(self.path(step["patch"]), i)
        info = None
        if step.get("date"):
            self.log(f"  run to {step['date']}")
            info = self.run_to(_date(step["date"]))
        if step.get("outfname"):
            if info is None:
                self.n_tmp += 1
                info = self.save_to(f"_runner_check_{self.n_tmp}")
            out = self.path(step["outfname"])
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(info["path"], out)
            res.update(outfname=str(out), sha256=_sha(out), bytes=out.stat().st_size)
        if info:
            res["date"] = info["date"]
        return res

    def apply_patch(self, module: Path, i: int) -> None:
        """Save, apply module.patch(text) -> text, reload the patched save (quit, Continue Game)."""
        spec = importlib.util.spec_from_file_location(f"patch_{i}", module)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.n_tmp += 1
        info = self.save_to(f"_runner_prepatch_{self.n_tmp}")
        text = Path(info["path"]).read_text(encoding="latin-1")
        patched = mod.patch(text)
        tmp = BRIDGE / "saves" / f"_runner_patched_{self.n_tmp}.eu4"
        tmp.write_text(patched, encoding="latin-1", newline="")
        self.log(f"  patch {module.name}: reloading")
        self.load_save(tmp)


def run_job(spec: dict, log=print, base: Path | None = None) -> dict:
    base = base or Path.cwd()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    bdir = BRIDGE / "runner_backup" / stamp
    bdir.mkdir(parents=True, exist_ok=True)
    files = [EU4 / "dlc_load.json", EU4 / "continue_game.json"]
    for f in files:
        shutil.copy2(f, bdir / f.name)
    r = Runner(spec, base, log)
    result: dict = {"ok": False, "steps": []}
    try:
        cfg = json.loads((EU4 / "dlc_load.json").read_text())
        cfg["enabled_mods"] = list(spec.get("mods", []))
        (EU4 / "dlc_load.json").write_text(json.dumps(cfg))
        log(f"start: {spec['nation']} {spec.get('base_save') or spec.get('start_date', '1444.11.11')}")
        r.start()
        for i, step in enumerate(spec.get("script", [])):
            log(f"step {i}: {step}")
            result["steps"].append(r.run_step(i, step))
        result["ok"] = True
    except Exception as e:  # noqa: BLE001
        result["error"] = f"{type(e).__name__}: {e}"
        log(f"FAILED: {result['error']}")
    finally:
        try:
            submit("quit", timeout=120)
        except Exception as e:  # noqa: BLE001
            log(f"quit failed: {e}")
        for f in files:
            shutil.copy2(bdir / f.name, f)
        for p in list(EU4.glob("automation_effects_*.txt")) + [SAVES / "automation_load.eu4"]:
            p.unlink(missing_ok=True)
        log("restored dlc_load.json and continue_game.json")
    return result


if __name__ == "__main__":
    job = Path(sys.argv[1]).resolve()
    out = run_job(json.loads(job.read_text()), base=job.parent)
    print(json.dumps(out, indent=1))
    sys.exit(0 if out["ok"] else 1)
