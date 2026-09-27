"""Client side of a file-based IPC bridge to a separate, unsandboxed "melt
worker" process (see `backend/tools/melt_worker.py`) that drives a real
headless-Chromium browser against https://pdx.tools to melt a binary
Ironman `.eu4` save into plain Clausewitz text -- without needing
Paradox's private EU4 token file ourselves (pdx.tools' own WASM build is
already compiled against it, on their end; melting then runs entirely
client-side in the visitor's browser tab, see that build's own README).

Why a separate process instead of just calling Playwright from here:
this backend often runs inside an agent/dev sandbox that blocks
arbitrary outbound network access (confirmed here: connecting to
pdx.tools or downloading a Chromium binary both fail at the OS/proxy
level), so it cannot itself reach pdx.tools. The melt worker is a small
standalone script a human starts by hand in an ordinary (unsandboxed)
terminal:

    source backend/.venv/bin/activate
    python3 backend/tools/melt_worker.py

which has full, unrestricted network/process access and does the actual
browser automation. This module and that worker never open a socket to
talk to each other -- they hand work off over a shared directory on
disk:

    <bridge_dir>/pending/<job_id>.eu4       -- we write the raw save here
    <bridge_dir>/processing/<job_id>.eu4    -- worker claims it (rename)
    <bridge_dir>/done/<job_id>.melted       -- worker writes melted text here
    <bridge_dir>/failed/<job_id>.error.txt  -- ...or an error message here
    <bridge_dir>/worker.heartbeat           -- worker refreshes this every
                                                few seconds, on its own
                                                thread, independent of
                                                whatever job it's working
                                                on (a melt can run far
                                                longer than the staleness
                                                threshold below)

`bridge_dir` defaults to `backend/.melt_bridge/` (override with
$MELT_BRIDGE_DIR); it's created on first use.

`melt()` drops a job, polls for either output with a timeout, and raises
PdxToolsMeltError either way (a worker-reported failure, or a timeout
with an actionable message telling the caller how to start the worker).
`available()` is a cheap, best-effort liveness check based on heartbeat
freshness -- it does not guarantee a given job will succeed (pdx.tools
could still be unreachable *from the worker's machine*, its page
structure could have changed, etc.), just that something is actively
polling the pending directory, so it's worth queuing a job at all.
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

DEFAULT_BRIDGE_DIR = Path(__file__).resolve().parent.parent.parent / ".melt_bridge"
HEARTBEAT_STALE_S = 10.0
DEFAULT_TIMEOUT_S = 180.0
POLL_INTERVAL_S = 0.25

WORKER_HINT = "source backend/.venv/bin/activate && python3 backend/tools/melt_worker.py"


class PdxToolsMeltError(RuntimeError):
    pass


def bridge_dir() -> Path:
    override = os.environ.get("MELT_BRIDGE_DIR")
    return Path(override) if override else DEFAULT_BRIDGE_DIR


def _dirs(bd: Path) -> tuple[Path, Path, Path]:
    pending, done, failed = bd / "pending", bd / "done", bd / "failed"
    for d in (pending, done, failed):
        d.mkdir(parents=True, exist_ok=True)
    return pending, done, failed


def available(bd: Path | None = None) -> bool:
    """Best-effort check that a melt worker process is alive and polling,
    based on the freshness of its heartbeat file."""
    heartbeat = (bd or bridge_dir()) / "worker.heartbeat"
    try:
        age = time.time() - heartbeat.stat().st_mtime
    except OSError:
        return False
    return age < HEARTBEAT_STALE_S


def melt(file_bytes: bytes, timeout: float = DEFAULT_TIMEOUT_S, bd: Path | None = None) -> bytes:
    """Hands `file_bytes` (the whole original `.eu4` zip) to the melt
    worker over the file bridge and returns the melted flat-text bytes it
    writes back. Raises PdxToolsMeltError on worker-reported failure or
    on timeout (including when no worker appears to be running at all)."""
    resolved_dir = bd or bridge_dir()
    pending, done, failed = _dirs(resolved_dir)

    job_id = uuid.uuid4().hex
    pending_path = pending / f"{job_id}.eu4"
    done_path = done / f"{job_id}.melted"
    failed_path = failed / f"{job_id}.error.txt"

    # Write atomically (same-directory rename) so the worker never picks
    # up a partially-written file.
    tmp_path = pending_path.with_suffix(".tmp")
    tmp_path.write_bytes(file_bytes)
    tmp_path.rename(pending_path)

    result: bytes | None = None
    error: str | None = None
    deadline = time.monotonic() + timeout
    try:
        while time.monotonic() < deadline:
            if done_path.exists():
                result = done_path.read_bytes()
                break
            if failed_path.exists():
                error = failed_path.read_text(encoding="utf-8", errors="replace").strip()
                break
            time.sleep(POLL_INTERVAL_S)
    finally:
        for p in (pending_path, done_path, failed_path):
            p.unlink(missing_ok=True)

    if result is not None:
        return result
    if error is not None:
        raise PdxToolsMeltError(error or "melt worker reported failure with no details")
    if not available(resolved_dir):
        raise PdxToolsMeltError(
            f"No melt worker is running (no fresh heartbeat under {resolved_dir}). "
            f"Start one in a normal, unsandboxed terminal with: {WORKER_HINT}"
        )
    raise PdxToolsMeltError(
        f"melt worker did not respond within {timeout:.0f}s (job {job_id}, bridge dir {resolved_dir})"
    )
