"""FastAPI app entrypoint.

Dev:  uvicorn app.main:app --reload --port 8000   (run `flutter run -d chrome` separately)
Prod: flutter build web   then this app serves frontend/build/web directly.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app import buildinfo
from app.api import router

app = FastAPI(title="EU4 Trade Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local tool; tighten if ever deployed publicly
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.middleware("http")
async def never_cache(request, call_next):
    # The Flutter bundle (main.dart.js) is loaded without a cache-buster, so
    # without this a browser can keep running an old build for days after a
    # `flutter build web`. Everything is served fresh; this is a local tool
    # on localhost, so re-downloading the bundle costs nothing.
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/build")
def get_build() -> dict:
    """Which frontend build is on disk right now (see app/buildinfo.py). The
    app polls this and warns when the page it is running is out of date."""
    return buildinfo.info()


def _index_with_build_id() -> HTMLResponse:
    """index.html with the on-disk build id stamped into <head>, so a loaded
    page knows exactly which build it is and can compare against /api/build."""
    html = (buildinfo.BUILD_DIR / "index.html").read_text(encoding="utf-8")
    stamp = f'<head>\n  <meta name="build-id" content="{buildinfo.build_id()}">'
    return HTMLResponse(html.replace("<head>", stamp, 1))


# Registered last: a Mount at "/" matches every path in FastAPI/Starlette's
# route list, so anything meant to be reachable (the API routes/health check
# above) must be registered before this or it'll be shadowed by the SPA's
# catch-all/index.html fallback.
FRONTEND_BUILD = buildinfo.BUILD_DIR
if FRONTEND_BUILD.exists():
    # Before the mount so these win over StaticFiles' plain index.html.
    app.add_api_route("/", _index_with_build_id, methods=["GET"], include_in_schema=False)
    app.add_api_route("/index.html", _index_with_build_id, methods=["GET"], include_in_schema=False)
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")
