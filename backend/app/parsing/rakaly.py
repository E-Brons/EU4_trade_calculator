"""Melts an Ironman `.eu4` save's binary `gamestate`/`meta` into the plain
Clausewitz text format our parser understands, with zero manual steps for
the person uploading the save.

Ironman saves are marked by a binary token stream that starts with the
`EU4bin` magic (as opposed to plain saves, which start with `EU4txt`).
Turning that back into field names needs Paradox's private EU4 token
dictionary, which isn't ours to distribute -- so melting has to happen
somewhere that either already has it, or already has a build that was
compiled against it. Two ways to get there, tried in order by
`melt_ironman_save()` below:

1. **pdx.tools browser automation** (`pdx_tools_melt.py`): pdx.tools ships
   a WASM build of the eu4save/jomini Rust libraries, already compiled
   against the token file on their end, and melts entirely client-side in
   the visitor's browser. We drive that from a small file-based IPC
   bridge to a separate, unsandboxed "melt worker" process
   (`backend/tools/melt_worker.py`) that a human starts once in an
   ordinary terminal -- see that module's docstring for why this can't
   just happen inline in this backend process, and for the on-disk
   protocol.
2. **A local `rakaly` CLI** (https://github.com/rakaly/cli) on
   `$RAKALY_PATH`/`PATH`/`backend/tools/rakaly`, for anyone who has
   separately obtained both the CLI and Paradox's token file. Kept as a
   manual escape hatch (`melt_bytes()` below); this is what a
   `RakalyNotFound`/`RakalyMeltError` refers to.

If neither is available, `melt_ironman_save()` raises `MeltUnavailableError`
with an actionable message: start the melt worker, install rakaly +
tokens, or melt manually via https://pdx.tools and re-upload the result
(already fully supported with zero extra parsing steps -- see save.py's
module docstring for that flat-text path).
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

BINARY_MAGIC = b"EU4bin"
TEXT_MAGIC = b"EU4txt"


class RakalyNotFound(RuntimeError):
    pass


class RakalyMeltError(RuntimeError):
    pass


class MeltUnavailableError(RuntimeError):
    """Raised when an Ironman save needs melting but neither automatic
    method (pdx.tools browser automation, local rakaly CLI) is available
    in this environment. The message is meant to be shown to the end
    user as-is: it names what was tried and how to fix it."""


def find_rakaly() -> Path | None:
    """Look for the rakaly binary, in order: $RAKALY_PATH, PATH, then a few
    conventional local install spots."""
    import os

    env_path = os.environ.get("RAKALY_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    on_path = shutil.which("rakaly")
    if on_path:
        return Path(on_path)

    for candidate in [
        Path(__file__).resolve().parent.parent.parent / "tools" / "rakaly",
        Path.home() / ".local" / "bin" / "rakaly",
    ]:
        if candidate.is_file():
            return candidate

    return None


def melt_bytes(data: bytes, rakaly_path: Path | None = None) -> bytes:
    """Runs `rakaly melt` on raw file bytes (a `gamestate` or `meta` member
    extracted from a `.eu4` zip) and returns the melted (plain text) bytes.

    Raises RakalyNotFound if no binary is available, or RakalyMeltError if
    rakaly ran but failed (e.g. missing tokens for this game version).
    """
    path = rakaly_path or find_rakaly()
    if path is None:
        raise RakalyNotFound(
            "rakaly CLI not found. Install it from https://github.com/rakaly/cli "
            "and either put it on PATH, set RAKALY_PATH, or place it at "
            "backend/tools/rakaly."
        )

    proc = subprocess.run(
        [str(path), "melt", "-o", "-", "-"],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RakalyMeltError(
            f"rakaly melt failed (exit {proc.returncode}): {proc.stderr.decode(errors='replace')[:2000]}"
        )
    return proc.stdout


def is_binary(data: bytes) -> bool:
    return data[:6] == BINARY_MAGIC


def is_text(data: bytes) -> bool:
    return data[:6] == TEXT_MAGIC


def ensure_text(data: bytes, rakaly_path: Path | None = None) -> bytes:
    """Returns `data` as plain Clausewitz text, melting it first if it's
    the binary Ironman format. Strips the magic header line either way so
    callers get a clean document to parse."""
    if is_binary(data):
        data = melt_bytes(data, rakaly_path)
    # Both text and freshly-melted data start with a magic line
    # (EU4txt / EU4txt again) followed by a newline; drop it.
    newline = data.find(b"\n")
    if newline != -1 and data[:6] in (TEXT_MAGIC, BINARY_MAGIC):
        data = data[newline + 1 :]
    return data


def melt_ironman_save(file_bytes: bytes, gamestate_raw: bytes, rakaly_path: Path | None = None) -> bytes:
    """Best-effort *automatic* melt of a whole binary Ironman `.eu4` file's
    bytes, for zero-manual-steps import via `/api/import-save`.

    `file_bytes` is the original save's full zip bytes (uploaded whole to
    pdx.tools, whose melt output merges meta+gamestate into one flat-text
    document); `gamestate_raw` is that zip's already-extracted `gamestate`
    member (melted alone via the rakaly CLI fallback, which only handles
    one member at a time).

    Tries, in order:
      1. pdx.tools browser automation over the file bridge in
         `pdx_tools_melt.py` -- needs a `melt_worker.py` process running
         (see that module), which in turn needs outbound network access
         to https://pdx.tools plus Playwright + a Chromium binary.
      2. A local `rakaly` CLI (`melt_bytes()` above) -- needs Paradox's
         private EU4 token file to be supplied separately by whoever set
         it up; kept as a manual escape hatch.

    Returns the melted document's raw bytes (still carrying its `EU4txt`
    magic line; callers should run the result through `ensure_text()` to
    strip that). Raises MeltUnavailableError, folding in what each path
    failed with, if neither works.
    """
    from app.parsing import pdx_tools_melt

    errors: list[str] = []

    if pdx_tools_melt.available():
        try:
            return pdx_tools_melt.melt(file_bytes)
        except pdx_tools_melt.PdxToolsMeltError as e:
            errors.append(f"pdx.tools automation: {e}")
    else:
        errors.append(f"pdx.tools automation: {pdx_tools_melt.WORKER_HINT}")

    path = rakaly_path or find_rakaly()
    if path is not None:
        try:
            return melt_bytes(gamestate_raw, path)
        except RakalyMeltError as e:
            errors.append(f"rakaly CLI: {e}")
    else:
        errors.append("rakaly CLI: not found (PATH, $RAKALY_PATH, or backend/tools/rakaly)")

    raise MeltUnavailableError(
        "This is an Ironman save (binary format) and it couldn't be melted "
        "automatically, so it can't be imported as-is. Tried: "
        + "; ".join(errors)
        + ". Workaround: open https://pdx.tools yourself, upload this save, "
        "open 'Save Info', click 'Melt', and re-upload the downloaded file "
        "here instead -- pre-melted files are accepted with zero extra "
        "steps. Or enter your trade data manually below."
    )
