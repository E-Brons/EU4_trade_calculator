#!/usr/bin/env python3
"""EU4 automation worker: the only process that drives the game (launch, keys, clicks, screenshots).

Run it in an ordinary iTerm tab (NOT through the agent's sandboxed shell), from the repo root:

    python3 tools/EU4-game-automation/worker.py

It needs iTerm2 in System Settings > Privacy & Security > Accessibility (keys/clicks) and, on the first
screenshot, Screen Recording. Leave it running; Ctrl-C stops it.

Protocol (client: bridge.py), all under tools/EU4-game-automation/.bridge/:
    pending/<id>.json      {"verb": ..., "args": {...}}       written by the client (tmp + rename)
    processing/<id>.json   claimed by the worker (rename)
    done/<id>.json         {"ok": true, "result": ...}
    failed/<id>.json       {"ok": false, "error": ...}
    worker.heartbeat       refreshed every 3 s
    shots/<name>.png       screenshots

Only the verbs in VERBS run; there is no way to execute arbitrary shell commands through the bridge.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRIDGE = HERE / ".bridge"
PENDING, PROCESSING, DONE, FAILED, SHOTS, BIN = (BRIDGE / d for d in ("pending", "processing", "done", "failed", "shots", "bin"))
HEARTBEAT = BRIDGE / "worker.heartbeat"
HELPER_SRC = HERE / "eu4input.swift"
HELPER = BIN / "eu4input"
GAME_APP = Path.home() / "Library/Application Support/Steam/steamapps/common/Europa Universalis IV/eu4.app"
APP_NAME = "eu4"

KEYS = {"enter": 36, "return": 36, "escape": 53, "esc": 53, "tab": 48, "space": 49, "grave": 50, "backspace": 51,
        "left": 123, "right": 124, "down": 125, "up": 126, "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96,
        "f6": 97, "f7": 98, "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111,
        "plus": 24, "minus": 27, "1": 18, "2": 19, "3": 20, "4": 21, "5": 23}

last_shot: dict = {}


def sh(*cmd: str, check: bool = True, timeout: float = 60) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> {r.returncode}: {(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def helper(*args: str, check: bool = True) -> str:
    if not HELPER.exists() or HELPER.stat().st_mtime < HELPER_SRC.stat().st_mtime:
        BIN.mkdir(parents=True, exist_ok=True)
        sh("swiftc", "-O", str(HELPER_SRC), "-o", str(HELPER), timeout=300)
    return sh(str(HELPER), *args, check=check)


def game_pid() -> int | None:
    for line in sh("ps", "-A", "-o", "pid=,comm=").splitlines():
        pid, _, comm = line.strip().partition(" ")
        if comm.strip().endswith("/eu4.app/Contents/MacOS/eu4"):
            return int(pid)
    return None


def front_game() -> None:
    if game_pid() is None:
        raise RuntimeError("eu4 is not running")
    front = helper("front")
    if APP_NAME not in front.lower() and "europa" not in front.lower():
        sh("open", "-a", str(GAME_APP))  # activates the running instance; no new launch
        time.sleep(0.5)
        front = helper("front")
    if APP_NAME not in front.lower() and "europa" not in front.lower():
        raise RuntimeError(f"could not bring eu4 to front (front app: {front!r})")


# ---------------------------------------------------------------- verbs
def v_ping() -> dict:
    return {"front_app": helper("front"), "accessibility_trusted": helper("trusted"), "game_pid": game_pid(),
            "game_window": helper("win", APP_NAME, check=False)}


def v_launch(args: list[str] | None = None) -> dict:
    if game_pid():
        return {"already_running": game_pid()}
    sh("open", "-a", str(GAME_APP), "--args", *(args if args is not None else ["-skiplauncher"]))
    for _ in range(120):
        time.sleep(1)
        if game_pid():
            return {"pid": game_pid()}
    raise RuntimeError("eu4 did not start within 120 s")


def v_quit(force: bool = False) -> dict:
    pid = game_pid()
    if not pid:
        return {"running": False}
    sh("kill", "-9" if force else "-TERM", str(pid))
    for _ in range(30):
        time.sleep(1)
        if not game_pid():
            return {"stopped": pid}
    raise RuntimeError(f"eu4 (pid {pid}) still running")


def v_key(name: str, shift: bool = False, repeat: int = 1) -> dict:
    front_game()
    code = KEYS[name.lower()] if not str(name).isdigit() or name in KEYS else int(name)
    for _ in range(repeat):
        helper("key", str(code), *(["shift"] if shift else []))
        time.sleep(0.05)
    return {"key": name, "code": code}


def v_keys(text: str) -> dict:
    front_game()
    helper("type", text)
    return {"typed": text}


def _console_probe(name: str = "_probe") -> tuple[bool, int]:
    """(console open?, bright pixels in its input box). Open console = a long horizontal border line (input box)
    at window y 660-740 (2048 px width): the median vertical gradient along x 30-600 is >= 70 there, the map
    gives < 55. Bright pixels (> 170) inside the box = typed text. Needs Pillow."""
    import statistics
    from PIL import Image
    info = v_shot(name)
    im = Image.open(info["path"]).convert("L")
    if im.width != 2048:
        im = im.resize((2048, round(im.height * 2048 / im.width)))
    px = im.load()
    best_g, best_y = 0.0, 0
    for y in range(660, 741):
        g = statistics.median(abs(px[x, y] - px[x, y - 2]) for x in range(30, 600, 3))
        if g > best_g:
            best_g, best_y = g, y
    if best_g < 70:
        return False, 0
    bright = sum(1 for y in range(max(best_y - 34, 0), min(best_y + 34, im.height)) for x in range(20, 600)
                 if px[x, y] > 170)
    return True, bright


def console_is_open() -> bool:
    return _console_probe()[0]


def _hover_console() -> None:
    """The console only takes keys while the cursor is over it (it turns see-through otherwise)."""
    helper("wmove", APP_NAME, "300", "450")  # window points; the window is 2048 points wide


def v_hover(x: float, y: float) -> dict:
    """Move the cursor to window-relative points (no click)."""
    front_game()
    return {"helper": helper("wmove", APP_NAME, f"{x:.0f}", f"{y:.0f}")}


def _ensure_console_open() -> None:
    _hover_console()
    for _ in range(3):
        if console_is_open():
            return
        helper("key", str(KEYS["grave"]))
        time.sleep(0.6)
    raise RuntimeError("console did not open (a pop-up may hold the keyboard focus)")


def _type_line(line: str) -> None:
    """Type into the open console and confirm the text arrived before pressing Enter; if the console ignores input,
    close and reopen it (the game's console sometimes stops reacting until toggled)."""
    for attempt in range(3):
        _ensure_console_open()
        helper("keyn", str(KEYS["backspace"]), "80")  # clear leftovers in the input field
        time.sleep(0.2)
        before = _console_probe()[1]
        helper("type", line)
        time.sleep(0.3)
        is_open, after = _console_probe()
        if is_open and after > before + 20:  # the text is in the input field
            helper("key", str(KEYS["enter"]))
            return
        helper("key", str(KEYS["grave"]))
        time.sleep(0.6)
    raise RuntimeError(f"console did not accept text: {line!r}")


def v_console(lines: list[str], close: bool = True, line_delay: float = 0.4, **_ignored) -> dict:
    """Run console lines. Never types unless the console is verifiably open (else keys become map hotkeys)."""
    front_game()
    for line in lines:
        _type_line(line)
        time.sleep(line_delay)
    if close and console_is_open():
        helper("key", str(KEYS["grave"]))
        time.sleep(0.4)
    return {"lines": lines, "console_open": console_is_open()}


def v_shot(name: str, whole_screen: bool = False) -> dict:
    SHOTS.mkdir(parents=True, exist_ok=True)
    out = SHOTS / f"{name}.png"
    win = None if whole_screen else helper("win", APP_NAME, check=False)
    if win and win[0].isdigit():
        wid, x, y, w, h = win.split()[:5]
        sh("screencapture", "-x", "-o", f"-l{wid}", str(out))
        bounds = [float(x), float(y), float(w), float(h)]
    else:
        sh("screencapture", "-x", str(out))
        bounds = None
    px = int(sh("sips", "-g", "pixelWidth", str(out)).split()[-1])
    py = int(sh("sips", "-g", "pixelHeight", str(out)).split()[-1])
    last_shot.update(path=str(out), bounds=bounds, size=[px, py])
    return dict(last_shot)


def v_click(x: float, y: float, space: str = "shot", mode: str = "hid") -> dict:
    """space="shot": pixel coordinates in the last screenshot of the game window (converted to window points and
    resolved against the window's position at click time); "screen": global points.
    mode: hid | session | pid | long (how the click events are delivered)."""
    front_game()
    if space == "shot":
        if not last_shot.get("bounds"):
            raise RuntimeError("no window screenshot yet; take a shot first")
        scale = last_shot["size"][0] / last_shot["bounds"][2]
        return {"helper": helper("wclick", APP_NAME, f"{x / scale:.1f}", f"{y / scale:.1f}", mode)}
    helper("click", f"{x:.1f}", f"{y:.1f}")
    return {"screen_point": [x, y]}


def v_screens() -> dict:
    return {"helper": helper("screens").splitlines()}


def v_fit_window() -> dict:
    """Move the game window onto a display large enough to show all of it (clicks only reach visible pixels)."""
    win = helper("win", APP_NAME).split()
    w, h = float(win[3]), float(win[4])
    displays = []
    for line in helper("screens").splitlines():
        m = re.search(r"cgBounds=\(([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+)\)", line)
        if m:
            displays.append(tuple(map(float, m.groups())))
    fits = [d for d in displays if d[2] >= w and d[3] >= h + 30]
    if not fits:
        raise RuntimeError(f"no display fits the {w:.0f}x{h:.0f} window: {displays}")
    dx, dy, dw, dh = max(fits, key=lambda d: d[2] * d[3])
    target = (dx + (dw - w) / 2, dy + 30)
    res = helper("movewin", APP_NAME, f"{target[0]:.0f}", f"{target[1]:.0f}")
    time.sleep(0.5)
    return {"move": res, "window_now": helper("win", APP_NAME)}


def v_cpu(samples: int = 3) -> dict:
    pid = game_pid()
    if not pid:
        raise RuntimeError("eu4 is not running")
    vals = []
    for _ in range(samples):
        vals.append(float(sh("ps", "-o", "%cpu=", "-p", str(pid))))
        time.sleep(0.5)
    return {"pid": pid, "cpu": vals}


def v_wait(seconds: float) -> dict:
    time.sleep(min(float(seconds), 600))
    return {"waited": seconds}


SAVE_DIR = Path.home() / "Documents/Paradox Interactive/Europa Universalis IV/save games"
OUT_DIR = BRIDGE / "saves"
_own_autosaves: set[int] = set()  # mtimes of autosaves written by this worker (no backup needed)


def v_save(name: str, timeout: float = 120) -> dict:
    """Write the current state with the console `autosave` command and copy it to .bridge/saves/<name>.eu4.
    The game rotates autosave -> old_autosave -> older_autosave on every autosave, so all three are copied aside first
    (to .bridge/autosave_backup/, once per file content) and the user's originals are never lost."""
    backup = BRIDGE / "autosave_backup"
    backup.mkdir(parents=True, exist_ok=True)
    for f in ("autosave.eu4", "old_autosave.eu4", "older_autosave.eu4"):
        src = SAVE_DIR / f
        if src.exists() and int(src.stat().st_mtime) not in _own_autosaves:  # rotation keeps mtimes
            dst = backup / f"{src.stem}.{int(src.stat().st_mtime)}.eu4"
            if not dst.exists():
                sh("cp", "-p", str(src), str(dst))
    before = (SAVE_DIR / "autosave.eu4").stat().st_mtime if (SAVE_DIR / "autosave.eu4").exists() else 0
    v_console(["autosave"], close=True)
    end = time.time() + timeout
    src = SAVE_DIR / "autosave.eu4"
    while time.time() < end:
        time.sleep(1)
        if src.exists() and src.stat().st_mtime > before:
            size = -1
            while size != src.stat().st_size:  # wait until the game stopped writing
                size = src.stat().st_size
                time.sleep(1)
            _own_autosaves.add(int(src.stat().st_mtime))
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            out = OUT_DIR / f"{name}.eu4"
            sh("cp", "-p", str(src), str(out))
            with open(out, "rb") as fh:
                head = fh.read(4096).decode("latin-1")
            date = re.search(r"\ndate=([\d.]+)", head)
            return {"path": str(out), "bytes": out.stat().st_size, "date": date.group(1) if date else None,
                    "format": head[:6]}
    raise RuntimeError("autosave.eu4 was not rewritten within the timeout")


REFS = HERE / "refs"


def _gray2048(path: str):
    from PIL import Image
    im = Image.open(path).convert("L")
    if im.width != 2048:
        im = im.resize((2048, round(im.height * 2048 / im.width)))
    return im


def v_screen() -> dict:
    """Which known screen is showing: mean abs difference of fixed UI crops against refs/*.png (match <= 15)."""
    from PIL import Image, ImageChops, ImageStat
    boxes = json.loads((REFS / "boxes.json").read_text())
    im = _gray2048(v_shot("_screen")["path"])
    scores = {}
    for k, b in boxes.items():
        ref = Image.open(REFS / f"{k}.png").convert("L")
        scores[k] = round(ImageStat.Stat(ImageChops.difference(ref, im.crop(tuple(b)))).mean[0], 1)
    best = min(scores, key=scores.get)
    return {"screen": best if scores[best] <= 15 else None, "scores": scores}


DATE_BOX = (1740, 46, 1900, 74)  # date text, top right, 2048 px window


def v_wait_stopped(max_s: float = 300, interval: float = 1.5, stable: int = 3) -> dict:
    """Wait until the date display stops changing (stable for `stable` consecutive comparisons)."""
    from PIL import ImageChops, ImageStat
    end = time.time() + float(max_s)
    prev, same, n = None, 0, 0
    while time.time() < end:
        cur = _gray2048(v_shot("_date")["path"]).crop(DATE_BOX)
        n += 1
        if prev is not None:
            d = ImageStat.Stat(ImageChops.difference(prev, cur)).mean[0]
            same = same + 1 if d < 1.0 else 0
            if same >= stable:
                return {"stopped": True, "samples": n}
        prev = cur
        time.sleep(float(interval))
    raise RuntimeError(f"game did not stop within {max_s}s")


VERBS = {"screen": v_screen, "wait_stopped": v_wait_stopped, "ping": v_ping, "launch": v_launch, "quit": v_quit, "key": v_key, "keys": v_keys, "console": v_console,
         "shot": v_shot, "click": v_click, "cpu": v_cpu, "wait": v_wait, "screens": v_screens,
         "fit_window": v_fit_window, "save": v_save, "hover": v_hover}


# ---------------------------------------------------------------- loop
def heartbeat_loop() -> None:
    while True:
        HEARTBEAT.write_text(str(time.time()))
        time.sleep(3)


def process(path: Path) -> None:
    claimed = PROCESSING / path.name
    try:
        path.rename(claimed)
    except FileNotFoundError:
        return
    job_id = path.stem
    try:
        job = json.loads(claimed.read_text())
        verb = job["verb"]
        if verb not in VERBS:
            raise ValueError(f"unknown verb {verb!r}; allowed: {sorted(VERBS)}")
        print(f"[{time.strftime('%H:%M:%S')}] {job_id} {verb} {job.get('args', {})}", flush=True)
        result = VERBS[verb](**job.get("args", {}))
        out, payload = DONE / f"{job_id}.json", {"ok": True, "result": result}
    except Exception as e:  # noqa: BLE001 - every failure goes back to the client
        traceback.print_exc()
        out, payload = FAILED / f"{job_id}.json", {"ok": False, "error": f"{type(e).__name__}: {e}"}
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload))
    tmp.rename(out)
    claimed.unlink(missing_ok=True)


def main() -> None:
    for d in (PENDING, PROCESSING, DONE, FAILED, SHOTS, BIN):
        d.mkdir(parents=True, exist_ok=True)
    helper("front")  # compile the helper up front so the first job is not slow
    # keep the displays awake while the worker runs: a sleeping external display drops out of the display list and
    # the game window then fits no screen (diversity batch 2026-10-07: 23 jobs lost)
    subprocess.Popen(["caffeinate", "-d", "-i", "-w", str(os.getpid())])
    threading.Thread(target=heartbeat_loop, daemon=True).start()
    print(f"EU4 automation worker ready. Bridge: {BRIDGE}  (Ctrl-C to stop)", flush=True)
    started = Path(__file__).stat().st_mtime
    while True:
        if Path(__file__).stat().st_mtime != started:  # code changed: restart in place, keep the same terminal
            print("worker.py changed - restarting", flush=True)
            os.execv(sys.executable, [sys.executable, *sys.argv])
        for p in sorted(PENDING.glob("*.json"), key=lambda q: q.stat().st_mtime):
            process(p)
        time.sleep(0.2)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
