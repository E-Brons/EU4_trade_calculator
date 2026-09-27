"""FastAPI app entrypoint.

Dev:  uvicorn app.main:app --reload --port 8000   (run `flutter run -d chrome` separately)
Prod: flutter build web   then this app serves frontend/build/web directly.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router

app = FastAPI(title="EU4 Trade Optimizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local tool; tighten if ever deployed publicly
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# Registered last: a Mount at "/" matches every path in FastAPI/Starlette's
# route list, so anything meant to be reachable (the API routes/health check
# above) must be registered before this or it'll be shadowed by the SPA's
# catch-all/index.html fallback.
FRONTEND_BUILD = Path(__file__).resolve().parent.parent.parent / "frontend" / "build" / "web"
if FRONTEND_BUILD.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")
