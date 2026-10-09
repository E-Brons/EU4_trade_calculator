#!/usr/bin/env python3
"""Headless screenshots of the built Flutter web app, with no listening socket.

Playwright serves a fake origin (http://app.test:8000/) by fulfilling requests
in-process: static files from --web-dir, /api/* through the FastAPI app via
starlette's TestClient. Any request to another origin is aborted and logged.

  backend/.venv/bin/python tools/shot.py --out /tmp/shot.png
  backend/.venv/bin/python tools/shot.py --steps steps.json --out /tmp/x.png

Steps (JSON list, or repeated --click-text), run after the dashboard loads:
  {"click_text": "Optimal"}   {"click": [x, y]}   {"wait": 800}
  {"wheel": [x, y, dy]}       {"drag": [x1, y1, x2, y2]}   {"key": "Escape"}
  {"shot": "name"}  -> saves <out stem>-name.png
The final screenshot always goes to --out. Text clicks use Flutter's semantics
tree (enabled automatically); fall back to "click": [x, y] if a label is missing.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from playwright.sync_api import sync_playwright  # noqa: E402

ORIGIN = "http://app.test:8000"  # port 8000 makes ApiClient use same-origin URLs
ROBOTO = Path("/opt/homebrew/share/flutter/bin/cache/artifacts/material_fonts/Roboto-Regular.ttf")
CHROMIUM_ARGS = [
    "--use-gl=angle",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
    "--enable-webgl",
]


def make_router(web_dir: Path, log):
    from fastapi.testclient import TestClient

    from app.main import app as api_app

    client = TestClient(api_app, base_url=ORIGIN)

    def handler(route):
        req = route.request
        if req.url.startswith("https://www.gstatic.com/flutter-canvaskit/"):
            # Default builds fetch CanvasKit from the CDN; serve the bundled copy.
            f = web_dir / "canvaskit" / req.url.split("?")[0].rsplit("/", 1)[1]
            if f.is_file():
                ctype = "application/wasm" if f.suffix == ".wasm" else "text/javascript"
                return route.fulfill(status=200, body=f.read_bytes(), headers={"content-type": ctype})
        if req.url.startswith("https://fonts.gstatic.com/") and ROBOTO.is_file():
            return route.fulfill(status=200, body=ROBOTO.read_bytes(), headers={"content-type": "font/ttf"})
        if not req.url.startswith(ORIGIN):
            log(f"BLOCKED external request: {req.url}")
            return route.abort()
        path = req.url[len(ORIGIN):].split("?")[0] or "/"
        if path.startswith("/api/"):
            headers = {k: v for k, v in req.headers.items() if k.lower() not in ("host", "content-length")}
            body = req.post_data_buffer
            r = client.request(req.method, path, content=body, headers=headers,
                               params=req.url.split("?", 1)[1] if "?" in req.url else None)
            out_headers = {k: v for k, v in r.headers.items() if k.lower() not in ("content-length", "content-encoding")}
            return route.fulfill(status=r.status_code, headers=out_headers, body=r.content)
        rel = path.lstrip("/") or "index.html"
        f = (web_dir / rel).resolve()
        if not f.is_file() or web_dir.resolve() not in f.parents:
            return route.fulfill(status=404, body="not found")
        ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
        if f.suffix == ".wasm":
            ctype = "application/wasm"
        return route.fulfill(status=200, body=f.read_bytes(), headers={"content-type": ctype, "cache-control": "no-store"})

    return handler


def enable_semantics(page):
    # Flutter hides an offscreen "Enable accessibility" button; clicking it builds the semantics tree.
    page.evaluate(
        """() => {
          const b = document.querySelector('flt-semantics-placeholder');
          if (b) b.click();
        }"""
    )
    page.wait_for_timeout(500)


def click_text(page, text, timeout=15000):
    enable_semantics(page)
    loc = page.locator("flt-semantics:not(:has(flt-semantics))").filter(has_text=text).first
    loc.wait_for(state="attached", timeout=timeout)
    box = loc.bounding_box()
    if box:
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    else:
        loc.click(force=True)


def run_step(page, step, out: Path, log):
    if "click_text" in step:
        click_text(page, step["click_text"])
    elif "click" in step:
        page.mouse.click(*step["click"])
    elif "wait" in step:
        page.wait_for_timeout(step["wait"])
    elif "wheel" in step:
        x, y, dy = step["wheel"]
        page.mouse.move(x, y)
        page.mouse.wheel(0, dy)
    elif "drag" in step:
        x1, y1, x2, y2 = step["drag"]
        page.mouse.move(x1, y1)
        page.mouse.down()
        page.mouse.move(x2, y2, steps=12)
        page.mouse.up()
    elif "key" in step:
        page.keyboard.press(step["key"])
    elif "shot" in step:
        p = out.with_name(f"{out.stem}-{step['shot']}{out.suffix}")
        page.screenshot(path=str(p))
        log(f"saved {p}")
    else:
        raise ValueError(f"unknown step {step}")
    page.wait_for_timeout(300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/shot.png")
    ap.add_argument("--web-dir", default=str(ROOT / "frontend/build/web"))
    ap.add_argument("--save", default="~/Downloads/Ottomans_Ironman_Backup_melted.eu4")
    ap.add_argument("--no-import", action="store_true", help="screenshot the import screen only")
    ap.add_argument("--size", default="1600x1000")
    ap.add_argument("--steps", help="JSON file with a list of steps")
    ap.add_argument("--ready-text", help="extra text that must be on screen before steps run")
    ap.add_argument("--click-text", action="append", default=[])
    ap.add_argument("--settle", type=int, default=3000, help="ms to wait after the dashboard appears")
    ap.add_argument("--timeout", type=int, default=240, help="seconds to wait for import+optimise")
    args = ap.parse_args()

    t0 = time.time()
    out = Path(args.out)
    w, h = (int(v) for v in args.size.split("x"))
    web_dir = Path(args.web_dir).expanduser()
    log = lambda m: print(f"[{time.time() - t0:5.1f}s] {m}", flush=True)

    steps = json.loads(Path(args.steps).read_text()) if args.steps else []
    steps += [{"click_text": t} for t in args.click_text]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=CHROMIUM_ARGS)
        ctx = browser.new_context(viewport={"width": w, "height": h})
        ctx.route("**/*", make_router(web_dir, log))
        page = ctx.new_page()
        page.on("console", lambda m: m.type in ("error", "warning") and "GL Driver Message" not in m.text and log(f"console.{m.type}: {m.text[:300]}"))
        page.on("pageerror", lambda e: log(f"pageerror: {e}"))
        page.goto(f"{ORIGIN}/", wait_until="load")
        page.wait_for_selector("flutter-view, flt-glass-pane", timeout=60000)
        page.wait_for_timeout(2500)
        log("app loaded")

        if args.no_import:
            page.screenshot(path=str(out))
            log(f"saved {out}")
        else:
            enable_semantics(page)
            save = Path(args.save).expanduser()
            with page.expect_file_chooser(timeout=20000) as fc:
                click_text(page, "Upload a .eu4 save")
            fc.value.set_files(str(save))
            log(f"uploaded {save.name}; waiting for dashboard")
            # The import screen's semantics disappear once the next route is pushed.
            leaf = "flt-semantics:not(:has(flt-semantics))"
            try:
                page.locator(leaf).filter(has_text="Upload a .eu4 save").first.wait_for(
                    state="detached", timeout=args.timeout * 1000)
                if args.ready_text:
                    enable_semantics(page)
                    page.locator(leaf).filter(has_text=args.ready_text).first.wait_for(
                        state="attached", timeout=args.timeout * 1000)
            except Exception:
                page.screenshot(path=str(out))
                log(f"dashboard never appeared; screenshot of current state saved to {out}")
                raise
            log("dashboard route open; settling")
            page.wait_for_timeout(args.settle)
            for s in steps:
                run_step(page, s, out, log)
            page.screenshot(path=str(out))
            log(f"saved {out}")
        browser.close()


if __name__ == "__main__":
    main()
