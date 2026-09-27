#!/usr/bin/env python3
"""Standalone melt worker for the EU4 Trade Calculator backend.

Run this in an ordinary, UNSANDBOXED terminal (Terminal.app, iTerm, a
plain shell -- not through an agent's sandboxed tool runner), because it
needs two things a sandboxed dev/agent environment may not have:

  1. Outbound network access to https://pdx.tools
  2. The ability to launch a real Chromium browser process

    cd EU4_Trade_calculator
    source backend/.venv/bin/activate      # or any venv with `playwright` installed
    playwright install chromium             # one-time, if not already done
    python3 backend/tools/melt_worker.py

Leave it running in the background while you use the app (Ctrl-C to
stop). It watches a directory for save files dropped by the backend's
`app.parsing.pdx_tools_melt` module, melts each one by driving a real
headless-Chromium tab against pdx.tools (upload -> "Save Info" -> click
"Melt" -> capture the resulting browser download), and writes the melted
plaintext back. See `app/parsing/pdx_tools_melt.py`'s module docstring
for the exact on-disk protocol (pending/processing/done/failed dirs +
heartbeat file) -- this script is the other end of it.

If the backend never sees this worker's heartbeat, it falls back to a
local `rakaly` CLI (if installed) and, failing that, returns a clear
error telling the user to either start this worker or melt+re-upload the
save manually via pdx.tools -- see `app/parsing/rakaly.py`.

Selectors used below were read directly out of the pdx.tools frontend
source (vendored at lib/pdx-tools), not guessed:
  - file input: `#analyze-box-file-input` (src/app/app/components/landing/HeroFileInput.tsx)
  - "Save Info" sidebar button, matched by accessible role+name rather
    than visible text: it's an icon-only, hover-to-expand sidebar item
    (src/app/app/features/eu4/Eu4CanvasOverlay.tsx renders
    `<InfoSideBarButton><span>Save Info</span><Icon/></InfoSideBarButton>`,
    a real `<button>` per SideBarButton.tsx) whose text label is visually
    clipped until a real mouse hover expands the sidebar's width -- a
    headless tab never hovers anything, so waiting for that text to be
    Playwright-"visible" hangs forever even though the button is fully
    real and clickable; force-clicking it directly is what actually
    works.
  - "Melt" button inside that panel (src/app/app/components/MeltButton.tsx),
    which triggers a real browser download (Blob + <a download>), not
    just an on-screen result.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from pathlib import Path

PDX_TOOLS_URL = "https://pdx.tools"
FILE_INPUT_SELECTOR = "#analyze-box-file-input"

NAV_TIMEOUT_MS = 20_000
ANALYZE_TIMEOUT_MS = 180_000  # a real multi-MB Ironman save's first-load client-side WASM parse can be slow
MELT_BUTTON_TIMEOUT_MS = 15_000
DOWNLOAD_TIMEOUT_MS = 60_000

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


def melt_via_browser(file_bytes: bytes, job_id: str) -> bytes:
    """Drives a real headless-Chromium tab against pdx.tools to melt a
    whole `.eu4` file's bytes, returning the melted flat-text document
    (meta + gamestate merged into one document -- same shape as any
    other manually pre-melted file our save.py already accepts)."""
    import tempfile

    from playwright.sync_api import sync_playwright

    with tempfile.TemporaryDirectory() as tmp_dir:
        upload_path = Path(tmp_dir) / "upload.eu4"
        upload_path.write_bytes(file_bytes)

        with sync_playwright() as pw:
            # Set MELT_WORKER_HEADFUL=1 to watch a real, visible browser
            # window step through the upload/melt flow -- much faster to
            # debug a stuck selector this way than iterating blind on
            # screenshots from a headless run.
            headless = os.environ.get("MELT_WORKER_HEADFUL") != "1"
            browser = pw.chromium.launch(
                headless=headless,
                # Headless Chromium disables real GPU access by default,
                # so pdx.tools detects "WebGL2 major performance caveat"
                # and shows a "browser not supported" banner instead of
                # proceeding past the upload screen -- confirmed via a
                # captured screenshot showing the site stuck on the
                # pristine landing page after upload. SwiftShader gives it
                # a working (software) WebGL2 implementation instead.
                args=[
                    "--use-gl=swiftshader",
                    "--enable-webgl",
                    "--enable-unsafe-swiftshader",
                    "--ignore-gpu-blocklist",
                ],
            )
            page = None
            try:
                page = browser.new_page()
                page.set_default_timeout(NAV_TIMEOUT_MS)

                # Capture browser-side console output/JS errors as they
                # happen -- a screenshot only shows the end state; this is
                # what actually explains a silent failure in the site's
                # own analysis pipeline (e.g. a WASM init error, a
                # rejected promise) that never surfaces as a Playwright
                # exception at all.
                console_log: list[str] = []
                page.on("console", lambda msg: console_log.append(f"[console.{msg.type}] {msg.text}"))
                page.on("pageerror", lambda exc: console_log.append(f"[pageerror] {exc}"))

                # Also watch the network directly: a completely silent
                # non-start (no analysis progress logged at all, not even
                # the first step) with no JS error either is consistent
                # with the WASM module or game-data fetch being blocked or
                # rate-limited server-side (pdx.tools sits behind
                # Cloudflare, confirmed via a CSP violation on
                # cloudflareinsights.com beacon in earlier runs) rather
                # than a client-side timing bug -- repeated automated
                # requests from the same fingerprint are exactly what
                # trips bot mitigation. A blocked/challenged fetch can
                # fail without ever surfacing as a page error.
                page.on(
                    "requestfailed",
                    lambda req: console_log.append(f"[requestfailed] {req.url} -- {req.failure}"),
                )
                page.on(
                    "response",
                    lambda res: console_log.append(f"[response {res.status}] {res.url}")
                    if res.status >= 400
                    else None,
                )

                # Force the classic <input type=file> upload flow instead
                # of the File System Access API's native OS file picker,
                # which headless automation can't drive.
                page.add_init_script("delete window.showOpenFilePicker;")

                # Root-cause fix for the "Your browser is not supported"
                # banner (see below): pdx.tools' own compatibility check
                # (compatibility.ts webgl2Compatibility()) creates a WebGL2
                # context with `failIfMajorPerformanceCaveat: true` and
                # treats a refusal as "performance caveat detected".
                # Headless Chromium's software (SwiftShader) renderer is
                # exactly a "major performance caveat" by definition, so
                # that check legitimately fails here even though the
                # context still works fine for actually parsing/melting a
                # save -- a real GPU-backed browser (confirmed: manual
                # Chrome use doesn't trigger this at all) never hits this
                # in the first place. Neutralize the flag at its source
                # instead of coping with the banner afterwards.
                page.add_init_script("""
                    (() => {
                        const orig = HTMLCanvasElement.prototype.getContext;
                        HTMLCanvasElement.prototype.getContext = function (type, attrs) {
                            if (attrs && attrs.failIfMajorPerformanceCaveat) {
                                attrs = { ...attrs, failIfMajorPerformanceCaveat: false };
                            }
                            return orig.call(this, type, attrs);
                        };
                    })();
                """)
                page.goto(PDX_TOOLS_URL, wait_until="domcontentloaded")

                file_input = page.locator(FILE_INPUT_SELECTOR)
                file_input.wait_for(state="attached", timeout=NAV_TIMEOUT_MS)

                # The "Save Info" sidebar button (icon + a "Save Info"
                # <span>, see Eu4CanvasOverlay.tsx) only renders once
                # client-side analysis of the uploaded save has finished,
                # so its presence is what we actually wait on. It's
                # visually an icon-only, collapsed sidebar item that only
                # reveals its text label on real mouse hover (a CSS width
                # transition) -- Playwright's `visible` state check treats
                # the clipped label as not visible and hangs forever, even
                # though the button is fully real and clickable. Match by
                # accessible role+name instead (unaffected by the visual
                # clipping).
                save_info_button = page.get_by_role("button", name="Save Info")

                # set_input_files occasionally doesn't register at all --
                # observed against a real save: the console log shows no
                # analysis progress whatsoever (no "load eu4 module" etc.),
                # just the page's own startup events. Likely a race
                # between `domcontentloaded` and React actually hydrating
                # the input's change handler. Retry the upload rather than
                # failing outright on one missed attempt, the same way the
                # Save Info click below does.
                #
                # A reload (not just re-selecting the file) is what the
                # retry actually needs: confirmed against a real save that
                # `input.files.length` reads back as 1 -- the file is
                # correctly attached -- on every single one of 6 retries
                # in a row, yet analysis never progresses even once. All 6
                # happen on the *same* loaded page with no navigation
                # between them, so this isn't 6 independent unlucky races;
                # it's one broken page session (something failed once at
                # load time -- most likely Worker/WASM init) that stays
                # broken for that page's whole lifetime, making every
                # further attempt against it equally futile. A fresh
                # `page.reload()` gives each retry an actual clean slate
                # instead of hammering the same stuck page.
                RETRY_UPLOAD_TIMEOUT_MS = 30_000
                upload_attempts = max(ANALYZE_TIMEOUT_MS // RETRY_UPLOAD_TIMEOUT_MS, 1)
                for attempt in range(1, upload_attempts + 1):
                    if save_info_button.count() == 0:
                        if attempt > 1:
                            page.reload(wait_until="domcontentloaded")
                            file_input.wait_for(state="attached", timeout=NAV_TIMEOUT_MS)
                        file_input.set_input_files(str(upload_path))
                        # Bisect "file never landed on the input at all"
                        # (a Playwright/browser-level issue) from "it
                        # landed but the app never reacted to it" (a
                        # site-level issue) -- the two look identical from
                        # the outside (silence either way).
                        try:
                            n_files = file_input.evaluate("el => el.files.length")
                            console_log.append(f"[diag] job {job_id} attempt {attempt}: input.files.length={n_files}")
                        except Exception as diag_exc:
                            console_log.append(f"[diag] job {job_id} attempt {attempt}: files.length check failed: {diag_exc}")
                    try:
                        save_info_button.wait_for(state="attached", timeout=RETRY_UPLOAD_TIMEOUT_MS)
                        break
                    except Exception:
                        if attempt == upload_attempts:
                            raise
                        print(f"[melt_worker] job {job_id}: upload attempt #{attempt} "
                              f"didn't start analysis, retrying (with a fresh page reload)...", flush=True)

                # Defensive fallback in case the monkeypatch above doesn't
                # cover every path to the banner (e.g. some other
                # detection route): explicitly check whether it's actually
                # present rather than blindly attempting a click and
                # swallowing the failure. `exact=True` is not optional
                # here: the sidebar's "Close Save" button (which resets
                # the whole analysis back to the landing page --
                # `onClick={() => actions.resetSaveAnalysis()}`) contains
                # "Close" as a substring too. Confirmed the hard way
                # against a real save: with the banner never showing
                # anymore (performanceCaveat: false, monkeypatch working),
                # this check with a substring match always found and
                # clicked "Close Save" instead -- silently wiping out a
                # fully successful analysis every time, well after the
                # real "load eu4 module" -> "first render" sequence had
                # already completed.
                close_button = page.get_by_role("button", name="Close", exact=True)
                if close_button.count() > 0:
                    close_button.evaluate("el => el.click()", timeout=3_000)

                melt_button = page.get_by_role("button", name="Melt").first
                # The click occasionally doesn't register as opening the
                # panel (observed against a real save: analysis succeeds,
                # the sidebar renders, but the Sheet never opens -- a
                # React-timing race, not a broken selector, since the same
                # click code does work most of the time). Retry a few
                # times rather than failing outright on one missed click;
                # each attempt is short so this still fails fast if the
                # button is genuinely never going to appear.
                #
                # Dispatch the click via the DOM (`el.click()`) instead of
                # Playwright's coordinate-based mouse simulation: even
                # force-clicking still resolves a screen (x, y) from the
                # element's bounding box and dispatches a real mouse event
                # there, which the browser then routes by hit-testing
                # whatever is actually topmost at that point. The
                # collapsed sidebar's hidden "Save Info" text label
                # apparently makes that computed box (or its center) land
                # somewhere over the map canvas instead of the visible
                # icon -- confirmed against a real save, where this
                # opened a province info popup underneath instead of the
                # sidebar panel, identically whether targeting the button
                # or its icon. `el.click()` triggers the element's click
                # handling directly, with no coordinates or hit-testing
                # involved at all, sidestepping that entirely.
                RETRY_CLICK_TIMEOUT_MS = 5_000
                attempts = max(MELT_BUTTON_TIMEOUT_MS // RETRY_CLICK_TIMEOUT_MS, 1)
                for attempt in range(1, attempts + 1):
                    # Don't re-click if the panel is already open from a
                    # previous attempt (only possible if wait_for below
                    # somehow raced past a button that WAS there) -- the
                    # Sheet trigger toggles, so a second click would close
                    # what the first one just opened.
                    if melt_button.count() == 0:
                        save_info_button.evaluate("el => el.click()", timeout=RETRY_CLICK_TIMEOUT_MS)
                    try:
                        melt_button.wait_for(state="attached", timeout=RETRY_CLICK_TIMEOUT_MS)
                        break
                    except Exception:
                        if attempt == attempts:
                            raise
                        # A stray click sometimes hits a province on the
                        # map underneath instead, opening ITS OWN details
                        # popup (a differently-styled Sheet -- white
                        # background, "<id>: <name>" title -- that reuses
                        # the exact same accessible "Close" button as
                        # every other Sheet in the app, see
                        # ProvinceSelectListener.tsx). If one is open,
                        # close it and give the map a moment to settle
                        # before retrying -- otherwise it can linger and
                        # keep intercepting the next attempt's click too.
                        if close_button.count() > 0:
                            close_button.evaluate("el => el.click()", timeout=3_000)
                            page.wait_for_timeout(1_000)
                        print(f"[melt_worker] job {job_id}: Save Info click #{attempt} "
                              f"didn't open the panel, retrying...", flush=True)
                # The info panel slides in from off-screen (a CSS
                # transition on the Sheet, see InfoSideBarButton.tsx); the
                # button is "attached" the instant the panel mounts, but
                # clicking immediately can hit it mid-slide, while it's
                # still positioned outside the viewport ("Element is
                # outside of the viewport", confirmed against a real
                # save). Waiting for "visible" isn't a reliable fix here
                # since a translated-but-still-`display`ed element can
                # already read as visible mid-transition -- just wait out
                # the transition instead.
                page.wait_for_timeout(500)

                with page.expect_download(timeout=DOWNLOAD_TIMEOUT_MS) as download_info:
                    melt_button.click(force=True)
                    # Random-new-world saves show a confirmation dialog
                    # with its own "Melt" button before the real download
                    # starts; click through it if (and only if) it shows up.
                    confirm_dialog = page.get_by_role("dialog").filter(has_text="random new world")
                    try:
                        confirm_dialog.get_by_role("button", name="Melt").click(timeout=3_000, force=True)
                    except Exception:
                        pass
                download = download_info.value
                melted_path = download.path()
                if melted_path is None:
                    raise RuntimeError("pdx.tools triggered a download but produced no file")
                return Path(melted_path).read_bytes()
            except Exception:
                # Capture what the page actually looked like at the point
                # of failure -- a headless timeout error message alone
                # ("waiting for X to be visible") doesn't say WHY X never
                # showed up (cookie banner, error toast, slow analysis,
                # a changed selector, a silent JS error...); the
                # screenshot/HTML/console log do.
                if page is not None:
                    try:
                        page.screenshot(path=str(FAILED_DIR / f"{job_id}.screenshot.png"), full_page=True)
                        (FAILED_DIR / f"{job_id}.page.html").write_text(page.content(), encoding="utf-8")
                        (FAILED_DIR / f"{job_id}.console.log").write_text(
                            "\n".join(console_log) or "(no console output captured)", encoding="utf-8"
                        )
                    except Exception:
                        pass  # diagnostics are best-effort; don't mask the real error
                raise
            finally:
                browser.close()


def process_one(pending_path: Path) -> None:
    job_id = pending_path.stem
    processing_path = PROCESSING_DIR / pending_path.name
    try:
        pending_path.rename(processing_path)
    except FileNotFoundError:
        return  # already claimed (shouldn't happen with a single worker, but be safe)

    print(f"[melt_worker] job {job_id}: melting via pdx.tools...", flush=True)
    try:
        melted = melt_via_browser(processing_path.read_bytes(), job_id)
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
