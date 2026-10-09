"""Run an existing ver_*/r* research script on the new saves U03/U04/U05 (and S79,S80 for reference) by overriding common.entries().
Usage: .venv/bin/python scripts/research/u345_pipe_runver.py ver_r08.py [ids comma list]"""
import sys, runpy
sys.path.insert(0, '.'); sys.path.insert(0, 'scripts/research')
import common
from u345_pipe_prev import NEW
script = sys.argv[1]
ids = (sys.argv[2] if len(sys.argv) > 2 else 'U03,U04,U05').split(',')
pool = {e['id']: e for e in common.entries() + NEW}
sel = [pool[i] for i in ids]
common.entries = lambda: sel
sys.argv = [script]
runpy.run_path(f'scripts/research/{script}', run_name='__main__')
