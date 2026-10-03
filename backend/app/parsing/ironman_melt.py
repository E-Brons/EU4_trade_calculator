"""Melts an Ironman `.eu4` save's binary `gamestate`/`meta` into the plain
Clausewitz text format our parser understands, with zero manual steps for
the person uploading the save.

Ironman saves are marked by a binary token stream that starts with the
`EU4bin` magic (as opposed to plain saves, which start with `EU4txt`).
Turning that back into field names needs Paradox's private EU4 token
dictionary, which isn't ours to distribute -- pdx.tools has one already
(its WASM build is compiled against it on their end, and melts entirely
client-side in the visitor's browser), so that's the one and only way
this melts a save: by driving a real browser against it. Two ways to get
there, tried in order by `melt_ironman_save()` below:

1. **In-process** (`pdx_tools_browser.py`): drives pdx.tools directly,
   right here in this backend process, with Playwright. This is the
   normal path and needs no setup beyond `playwright install chromium`
   once -- it only fails to even attempt this when Playwright/a browser
   binary genuinely isn't available in this environment (e.g. a
   sandboxed agent/dev run that blocks outbound network and browser
   launches from its own process tree).
2. **A separate, already-running "melt worker" process**
   (`pdx_tools_melt.py`'s file-bridge client), for exactly that sandboxed
   case: a human starts `backend/tools/melt_worker.py` once in an
   ordinary, unsandboxed terminal, and this backend hands jobs to it over
   a shared directory instead of attempting the browser itself. Not
   needed for a normal (unsandboxed) run of this backend.

If neither works, `melt_ironman_save()` raises `MeltUnavailableError` with
an actionable message: install playwright/chromium, start the melt
worker, or melt manually via https://pdx.tools and re-upload the result
(already fully supported with zero extra parsing steps -- see save.py's
module docstring for that flat-text path).
"""
from __future__ import annotations

BINARY_MAGIC = b"EU4bin"
TEXT_MAGIC = b"EU4txt"


class MeltUnavailableError(RuntimeError):
    """Raised when an Ironman save needs melting but neither automatic
    method (in-process pdx.tools automation, a separate melt worker) is
    available in this environment. The message is meant to be shown to
    the end user as-is: it names what was tried and how to fix it."""


def is_binary(data: bytes) -> bool:
    return data[:6] == BINARY_MAGIC


def is_text(data: bytes) -> bool:
    return data[:6] == TEXT_MAGIC


def ensure_text(data: bytes) -> bytes:
    """Strips the magic header line (`EU4txt`/`EU4bin`) from already-text
    data so callers get a clean document to parse. `data` must already be
    plain text by this point (melted, if it started out binary) --
    callers are responsible for calling `melt_ironman_save()` first if
    `is_binary(data)`."""
    newline = data.find(b"\n")
    if newline != -1 and data[:6] in (TEXT_MAGIC, BINARY_MAGIC):
        data = data[newline + 1 :]
    return data


def melt_ironman_save(file_bytes: bytes) -> bytes:
    """Best-effort *automatic* melt of a whole binary Ironman `.eu4` file's
    bytes, for zero-manual-steps import via `/api/import-save`.

    `file_bytes` is the original save's full zip bytes, uploaded whole to
    pdx.tools (whose melt output merges meta+gamestate into one flat-text
    document).

    Tries, in order:
      1. pdx.tools browser automation, directly in this process (see
         `pdx_tools_browser.melt_via_browser`) -- needs Playwright plus a
         Chromium binary available right here; this is the normal path
         and needs no separate process.
      2. The same automation, but handed off to an already-running
         separate `melt_worker.py` process over the file bridge in
         `pdx_tools_melt.py` -- only matters when step 1 can't even be
         attempted in this process (e.g. a sandboxed agent/dev run).

    Returns the melted document's raw bytes (still carrying its `EU4txt`
    magic line; callers should run the result through `ensure_text()` to
    strip that). Raises MeltUnavailableError, folding in what each path
    failed with, if neither works.
    """
    errors: list[str] = []

    try:
        from app.parsing.pdx_tools_browser import melt_via_browser

        return melt_via_browser(file_bytes)
    except Exception as e:
        errors.append(f"pdx.tools automation (in-process): {e}")

    from app.parsing import pdx_tools_melt

    if pdx_tools_melt.available():
        try:
            return pdx_tools_melt.melt(file_bytes)
        except pdx_tools_melt.PdxToolsMeltError as e:
            errors.append(f"pdx.tools automation (separate worker): {e}")
    else:
        errors.append(f"pdx.tools automation (separate worker): {pdx_tools_melt.WORKER_HINT}")

    raise MeltUnavailableError(
        "This is an Ironman save (binary format) and it couldn't be melted "
        "automatically, so it can't be imported as-is. Tried: "
        + "; ".join(errors)
        + ". Workaround: open https://pdx.tools yourself, upload this save, "
        "open 'Save Info', click 'Melt', and re-upload the downloaded file "
        "here instead -- pre-melted files are accepted with zero extra "
        "steps. Or enter your trade data manually below."
    )
