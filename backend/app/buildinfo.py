"""Identity of the built Flutter bundle, so a browser tab can tell whether it is
running the build that is currently on disk (and whether the sources have
changed since that build).

The build id is a short hash of `frontend/build/web/main.dart.js`: it changes
exactly when the compiled app changes, with no build-script cooperation.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
BUILD_DIR = FRONTEND_DIR / "build" / "web"
BUNDLE = BUILD_DIR / "main.dart.js"

# Things whose modification means "the app would look different if rebuilt".
_SOURCE_ROOTS = [FRONTEND_DIR / "lib", FRONTEND_DIR / "web"]
_SOURCE_FILES = [FRONTEND_DIR / "pubspec.yaml"]

_hash_cache: tuple[float, int, str] | None = None


def build_id() -> str | None:
    """Short hash of the served bundle; None if the frontend isn't built."""
    global _hash_cache
    try:
        st = BUNDLE.stat()
    except FileNotFoundError:
        return None
    if _hash_cache and _hash_cache[:2] == (st.st_mtime, st.st_size):
        return _hash_cache[2]
    digest = hashlib.sha256()
    with BUNDLE.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    _hash_cache = (st.st_mtime, st.st_size, digest.hexdigest()[:8])
    return _hash_cache[2]


def built_at() -> str | None:
    try:
        ts = BUNDLE.stat().st_mtime
    except FileNotFoundError:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def sources_newer_than_build() -> bool:
    """True if any frontend source file was modified after the bundle was built."""
    try:
        built = BUNDLE.stat().st_mtime
    except FileNotFoundError:
        return False
    candidates = list(_SOURCE_FILES)
    for root in _SOURCE_ROOTS:
        if root.exists():
            candidates.extend(p for p in root.rglob("*") if p.is_file())
    for p in candidates:
        try:
            if p.stat().st_mtime > built:
                return True
        except FileNotFoundError:
            continue
    return False


def info() -> dict:
    return {
        "build_id": build_id(),
        "built_at": built_at(),
        "sources_newer_than_build": sources_newer_than_build(),
    }
