#!/usr/bin/env python3
"""Stdio MCP server for the EU4 automation worker (JSON-RPC 2.0, newline-delimited, stdlib only).

Every game action is forwarded to worker.py through bridge.submit (file bridge). The worker must be running in the
user's own terminal: python3 tools/EU4-game-automation/worker.py
"""
from __future__ import annotations

import base64
import json
import sys
import threading
import time
import traceback
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bridge  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SAVES = HERE / ".bridge" / "saves"

COMMON = ("One EU4 instance is driven by one worker; calls are serialized. Requires worker.py running in the "
          "user's own terminal (outside the agent sandbox).")

TOOLS = [
    {"name": "eu4_ping", "description": f"Check the worker: front app, Accessibility trust, game pid/window. {COMMON}",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "eu4_launch", "description": "Start EU4 (straight to the main menu via -skiplauncher). No-op if running.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "eu4_quit", "description": "Stop the EU4 process (unsaved state is lost; save first with eu4_save).",
     "inputSchema": {"type": "object", "properties": {"force": {"type": "boolean"}}}},
    {"name": "eu4_fit_window",
     "description": "Move the game window onto a display that shows all of it. Clicks only reach visible pixels; "
                    "call after launch when the window is larger than the current screen.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "eu4_screenshot",
     "description": "Screenshot of the game window, returned as an image. Click coordinates refer to this image's pixels.",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}}},
    {"name": "eu4_click",
     "description": "Left click at pixel (x, y) of the LAST screenshot (take one first). Clicking the map selects "
                    "provinces and opens windows that block the console.",
     "inputSchema": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                     "required": ["x", "y"]}},
    {"name": "eu4_key",
     "description": "Press one key: enter, escape, space (pause toggle), grave (console), f1-f12, arrows, ... "
                    "Keys while the console is closed are game hotkeys.",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "eu4_console",
     "description": "Run console commands, one per line (list: tools/EU4-game-automation/commands_1.37.5.md). The worker "
                    "types only when the console is verified open and the text arrived (else letters would be map "
                    "hotkeys). Useful: 'observe' = spectator mode (AI runs every country and answers events, so no "
                    "pop-ups pause the game); 'tag VEN' = play a country again; 'stop YYYY.MM.DD' + 'speed 5' = run "
                    "and pause exactly on that date; 'run <file>' = effects file from the EU4 user folder.",
     "inputSchema": {"type": "object", "properties": {"lines": {"type": "array", "items": {"type": "string"}},
                                                      "close": {"type": "boolean"}}, "required": ["lines"]}},
    {"name": "eu4_wait_stopped",
     "description": "Wait until the game is paused (e.g. after 'stop <date>' + 'speed 5').",
     "inputSchema": {"type": "object", "properties": {"timeout": {"type": "number"}}}},
    {"name": "eu4_save",
     "description": "Save the current state (console 'autosave', the rotating autosave slots are backed up first) "
                    "and copy it to .bridge/saves/<name>.eu4. Returns path, size, and the date read from the file.",
     "inputSchema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "eu4_run_job",
     "description": "Run a declarative job in the background: {nation, start_date, mods, script: [{console_commands, "
                    "date, outfname}, ...]}. Returns job_id; poll eu4_job_status. One job at a time.",
     "inputSchema": {"type": "object", "properties": {"spec": {"type": "object"}}, "required": ["spec"]}},
    {"name": "eu4_job_status", "description": "State (running/done/failed), log lines and result of a job.",
     "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]}},
    {"name": "eu4_list_saves", "description": "Saves produced so far in .bridge/saves (name, bytes, modified).",
     "inputSchema": {"type": "object", "properties": {}}},
]

# tool -> (worker verb, timeout s)
FORWARD = {"eu4_ping": ("ping", 60), "eu4_launch": ("launch", 180), "eu4_quit": ("quit", 60),
           "eu4_fit_window": ("fit_window", 60), "eu4_click": ("click", 60), "eu4_key": ("key", 60),
           "eu4_console": ("console", 300), "eu4_save": ("save", 300)}

JOBS: dict[str, dict] = {}
JOB_LOCK = threading.Lock()


def _start_job(spec: dict) -> dict:
    with JOB_LOCK:
        if any(j["state"] == "running" for j in JOBS.values()):
            raise RuntimeError("a job is already running")
        job_id = uuid.uuid4().hex[:8]
        job = {"state": "running", "log": [], "result": None, "started": time.time()}
        JOBS[job_id] = job

    def log(msg) -> None:
        job["log"].append(f"{time.strftime('%H:%M:%S')} {msg}")

    def target() -> None:
        try:
            from runner import run_job
            try:
                job["result"] = run_job(spec, log=log)
            except TypeError:
                job["result"] = run_job(spec)
            job["state"] = "done"
        except Exception as e:  # noqa: BLE001
            job["state"] = "failed"
            job["result"] = f"{type(e).__name__}: {e}"
            log(traceback.format_exc())

    threading.Thread(target=target, daemon=True).start()
    return {"job_id": job_id}


def call_tool(name: str, args: dict) -> list[dict]:
    if name in FORWARD:
        verb, timeout = FORWARD[name]
        return [{"type": "text", "text": json.dumps(bridge.submit(verb, timeout=timeout, **args), indent=1)}]
    if name == "eu4_wait_stopped":
        t = float(args.get("timeout", 600))
        return [{"type": "text", "text": json.dumps(bridge.submit("wait_stopped", timeout=t + 30, **args))}]
    if name == "eu4_screenshot":
        res = bridge.submit("shot", timeout=60, name=args.get("name", "mcp"))
        data = base64.b64encode(Path(res["path"]).read_bytes()).decode()
        return [{"type": "image", "data": data, "mimeType": "image/png"},
                {"type": "text", "text": json.dumps(res)}]
    if name == "eu4_run_job":
        return [{"type": "text", "text": json.dumps(_start_job(args["spec"]))}]
    if name == "eu4_job_status":
        job = JOBS.get(args["job_id"])
        if job is None:
            raise KeyError(f"unknown job {args['job_id']}")
        return [{"type": "text", "text": json.dumps(job, default=str, indent=1)}]
    if name == "eu4_list_saves":
        rows = [{"name": p.name, "bytes": p.stat().st_size,
                 "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))}
                for p in sorted(SAVES.glob("*.eu4"))] if SAVES.exists() else []
        return [{"type": "text", "text": json.dumps(rows, indent=1)}]
    raise KeyError(f"unknown tool {name}")


def handle(msg: dict) -> dict | None:
    method, mid = msg.get("method"), msg.get("id")
    if mid is None:  # notification
        return None
    try:
        if method == "initialize":
            result = {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {}},
                      "serverInfo": {"name": "eu4-automation", "version": "0.1.0"}}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            p = msg.get("params", {})
            try:
                result = {"content": call_tool(p["name"], p.get("arguments") or {}), "isError": False}
            except Exception as e:  # noqa: BLE001 - tool errors are results, not protocol errors
                result = {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True}
        elif method == "ping":
            result = {}
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    except Exception as e:  # noqa: BLE001
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}


def main() -> None:
    out_lock = threading.Lock()

    def respond(msg: dict) -> None:
        resp = handle(msg)
        if resp is not None:
            with out_lock:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        # tool calls can block for minutes; answer them on threads so pings/status stay responsive
        threading.Thread(target=respond, args=(msg,), daemon=True).start()


if __name__ == "__main__":
    main()
