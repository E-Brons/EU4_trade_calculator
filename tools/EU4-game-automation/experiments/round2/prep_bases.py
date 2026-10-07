#!/usr/bin/env python3
"""Extract round-2 bases that live in datasets/ as LFS zips (the runner needs a plain .eu4). Run once before the batch."""
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASES = {"U10_VEN.1444.12.01.eu4": ROOT / "datasets/eu4/1.37.5/vanilla/dlc-819b35e6/venice-1444/U10_VEN.1444.12.01.eu4.zip"}

if __name__ == "__main__":
    out = HERE / "bases"
    out.mkdir(exist_ok=True)
    for name, z in BASES.items():
        with zipfile.ZipFile(z) as f:
            (out / name).write_bytes(f.read(name))
        print("extracted", out / name)
