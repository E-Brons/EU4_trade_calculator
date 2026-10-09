import sys
sys.path.insert(0, "scripts/research")
import venice_load as V
from pathlib import Path
V.load(Path(sys.argv[1]), "provinces"); print(sys.argv[1])
