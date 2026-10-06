"""POST /api/verify-save: checks an uploaded save against the calculation and stores it as a RED case on mismatch."""
from __future__ import annotations

import os
import tempfile
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.parsing import ironman_melt
from app.parsing.tradenodes import load_trade_graph
from app.trade import cases, savefile
from app.trade.extract import extract_world
from app.trade.verify import verify_world

router = APIRouter(prefix="/api")


def _summary(report) -> dict:
    d = report.to_dict()
    for s in d["stages"].values():
        s["worst"] = s["worst"][:5]
    d["chain"]["worst"] = d["chain"]["worst"][:5]
    return d


@router.post("/verify-save")
async def verify_save(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".eu4") as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            text = savefile.read_save_text(Path(tmp.name))
            world = extract_world(Path(tmp.name), file.filename or "upload", graph=load_trade_graph())
        except ironman_melt.MeltUnavailableError as e:
            raise HTTPException(422, str(e)) from e
        except zipfile.BadZipFile as e:
            raise HTTPException(422, f"Not a valid .eu4 save file: {e}") from e
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
    report = verify_world(world)
    stored = None
    if report.status != "verified" and os.environ.get("EU4_STORE_CASES", "1") != "0":
        stored = cases.store_case(text, report)
    if report.status == "verified":
        message = "The calculation reproduces every number recorded in this save."
    else:
        where = report.first_failing_stage or "the end-to-end chain"
        message = (
            f"Our calculation does not reproduce this save (first failing stage: {where}). Results for it are unverified. "
            + (f"The save was stored as case {stored.id} for investigation." if stored and not stored.duplicate
               else f"This save is already stored as case {stored.id}." if stored else "")
        ).strip()
    return {"verification": _summary(report), "stored_case": stored.id if stored else None, "message": message}
