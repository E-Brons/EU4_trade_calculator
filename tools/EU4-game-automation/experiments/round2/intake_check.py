"""Dry-run of the dataset intake (backend/app/trade/intake.py) into a temporary root: tells whether saves would be
accepted, without touching datasets/. Run from backend/ with the venv:
    .venv/bin/python ../tools/EU4-game-automation/experiments/round2/intake_check.py <series> <role>:<save> [<role>:<save> ...]
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from app.trade import intake  # noqa: E402

series, pairs = sys.argv[1], sys.argv[2:]
root = Path(tempfile.mkdtemp(prefix="intake_check_"))
for p in pairs:
    role, save = p.split(":", 1)
    try:
        a = intake.add_save(Path(save), series, role, change=f"dry run {role}", root=root)
        print(f"{role}: accepted ({a.id}); placements changed vs A: {a.placements_changed}")
    except intake.Rejected as e:
        print(f"{role}: REJECTED: {e}")
