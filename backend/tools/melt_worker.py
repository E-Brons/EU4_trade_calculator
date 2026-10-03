#!/usr/bin/env python3
"""Standalone melt worker for the EU4 Trade Calculator backend.

This is an OPTIONAL fallback, not required for normal use. As of this
version, `ironman_melt.melt_ironman_save()` first tries driving pdx.tools
directly, in-process, inside the backend's own request handler (see
`app.parsing.pdx_tools_browser.melt_via_browser`) -- which works fine
for an ordinary (unsandboxed) run of this backend, with zero manual
setup beyond `playwright install chromium` once.

This separate worker only still matters for environments that can't do
that *in-process* -- e.g. an agent/dev sandbox that blocks outbound
network access and browser launches from its own sandboxed process
tree, but can still start an ordinary, unsandboxed process by hand that
has no such restriction. If that's not your situation, you don't need
to run this at all.

Run this in an ordinary, UNSANDBOXED terminal (Terminal.app, iTerm, a
plain shell -- not through an agent's sandboxed tool runner):

    cd EU4_Trade_calculator
    source backend/.venv/bin/activate      # or any venv with `playwright` installed
    playwright install chromium             # one-time, if not already done
    python3 backend/tools/melt_worker.py

Leave it running in the background while you use the app (Ctrl-C to
stop). It watches a directory for save files dropped by the backend's
`app.parsing.pdx_tools_melt` module (only reached if the in-process
attempt above raised), melts each one via
`pdx_tools_browser.melt_via_browser`, and writes the melted plaintext
back. See `app/parsing/pdx_tools_melt.py`'s module docstring for the
exact on-disk protocol (pending/processing/done/failed dirs +
heartbeat file) -- this script is the other end of it.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Must stay well under pdx_tools_melt.py's HEARTBEAT_STALE_S (10s) -- see
# main()'s heartbeat thread for why this can't just be "once per job".
HEARTBEAT_INTERVAL_S = 3.0

BRIDGE_DIR = Path(os.environ.get("MELT_BRIDGE_DIR", Path(__file__).resolve().parent.parent / ".melt_bridge"))
PENDING_DIR = BRIDGE_DIR / "pending"
PROCESSING_DIR = BRIDGE_DIR / "processing"
DONE_DIR = BRIDGE_DIR / "done"
FAILED_DIR = BRIDGE_DIR / "failed"
HEARTBEAT_PATH = BRIDGE_DIR / "worker.heartbeat"

POLL_INTERVAL_S = 1.0


def process_one(pending_path: Path) -> None:
    from app.parsing.pdx_tools_browser import melt_via_browser

    job_id = pending_path.stem
    processing_path = PROCESSING_DIR / pending_path.name
    try:
        pending_path.rename(processing_path)
    except FileNotFoundError:
        return  # already claimed (shouldn't happen with a single worker, but be safe)

    print(f"[melt_worker] job {job_id}: melting via pdx.tools...", flush=True)
    try:
        melted = melt_via_browser(processing_path.read_bytes(), diagnostics_dir=FAILED_DIR, label=job_id)
        (DONE_DIR / f"{job_id}.melted").write_bytes(melted)
        print(f"[melt_worker] job {job_id}: done ({len(melted)} bytes)", flush=True)
    except Exception as e:
        detail = f"pdx.tools automation failed: {e}"
        (FAILED_DIR / f"{job_id}.error.txt").write_text(detail, encoding="utf-8")
        print(f"[melt_worker] job {job_id}: FAILED: {detail}", flush=True)
        traceback.print_exc()
    finally:
        processing_path.unlink(missing_ok=True)


def main() -> None:
    for d in (PENDING_DIR, PROCESSING_DIR, DONE_DIR, FAILED_DIR):
        d.mkdir(parents=True, exist_ok=True)

    try:
        import playwright  # noqa: F401
    except ImportError:
        print(
            "playwright is not installed in this Python environment.\n"
            "Install it with: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[melt_worker] watching {PENDING_DIR} (Ctrl-C to stop)", flush=True)

    # Heartbeat on its own thread, ticking continuously regardless of what
    # the main loop is doing. Getting this wrong is exactly the bug that
    # motivated it: the main loop used to touch the heartbeat only
    # *between* jobs, but pdx_tools_melt.py's client treats it stale after
    # just 10s (HEARTBEAT_STALE_S) -- far shorter than a real multi-MB
    # save's melt can take -- so a client mid-poll would see a stale
    # heartbeat and wrongly report "no worker running" while this process
    # was very much alive and working, just busy.
    stop_heartbeat = threading.Event()

    def _heartbeat_loop() -> None:
        while not stop_heartbeat.is_set():
            HEARTBEAT_PATH.write_text(str(time.time()))
            stop_heartbeat.wait(HEARTBEAT_INTERVAL_S)

    heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    try:
        while True:
            for p in sorted(PENDING_DIR.glob("*.eu4")):
                process_one(p)
            time.sleep(POLL_INTERVAL_S)
    except KeyboardInterrupt:
        print("\n[melt_worker] stopping.", flush=True)
    finally:
        stop_heartbeat.set()


if __name__ == "__main__":
    main()
