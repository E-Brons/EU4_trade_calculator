import sys, json
from pathlib import Path
sys.path.insert(0, ".")
from app.parsing.tradenodes import load_trade_graph
from app.trade.extract import extract_world
from app.trade.verify import verify_world
g = load_trade_graph()
FIX = Path("tests/fixtures/saves")
files = {"U03": "U03_TUR.1691.01.09.eu4", "U04": "U04_TUR.1691.11.01.eu4", "U05": "U05_TUR.1693.04.15.eu4", "U06": "U06_TUR.1696.03.25.eu4"}
res = {}
for sid, fn in files.items():
    r = verify_world(extract_world(FIX / fn, sid, graph=g))
    res[sid] = r
    print(sid, r.date, r.status, "first failing:", r.first_failing_stage, "unmapped:", r.unmapped_keys)
names = list(res["U06"].stages)
print("stage".ljust(20), *[s.ljust(14) for s in res])
for n in names:
    cells = []
    for sid in res:
        st = res[sid].stages[n]
        cells.append(f"{st.failures}/{st.checks}".ljust(14) if st.status != "not_implemented" else "n/i".ljust(14))
    print(n.ljust(20), *cells)
print("chain:", {sid: (res[sid].chain.status, res[sid].chain.failures, res[sid].chain.checks) for sid in res})
for sid in ("U06",):
    for n in names:
        st = res[sid].stages[n]
        if st.failures:
            print(sid, n, "worst:", [(w.node, w.tag, round(w.predicted, 3), round(w.recorded, 3)) for w in st.worst[:4]])
