"""Second-pass check: run the project's verification over every save in the manifest and dump per-stage checks/failures."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, ".")
from app.trade import corpus
out = {}
t = time.time()
def prog(i): print(i, round(time.time()-t), flush=True)
rep = corpus.run_corpus(progress=prog)
for sid, r in rep.reports.items():
    out[sid] = {"date": r.date, "status": r.status, "first": r.first_failing_stage,
                "stages": {s: [x.status, x.checks, x.failures, round(x.max_abs_error, 4)] for s, x in r.stages.items()},
                "chain": [r.chain.status, r.chain.note[:80], r.chain.checks, r.chain.failures]}
Path("/tmp/eu4research/ver2_stages.json").write_text(json.dumps(out, indent=1))
print("done", len(out), "missing", rep.missing)
