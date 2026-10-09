"""R10 final, shared helper: embargoed-country rows of the whole corpus, built from raw save blocks only
(countries, provinces, trade nodes; no app.trade.calc code).

One row = (save, embargoed tag, node) for a country with a non-empty `trade_embargoed_by` that has an entry (max_demand) at the node.
  md      max_demand of the entry, doubled when the entry is an away collector (key `total` without `has_capital`), i.e. the R02 factor 0.5 undone
  cap     modal md of the same country in the same class (domestic / foreign) over the nodes where no embargoer has own power
  class   domestic = node of the country's `trade_port` province or the country is `top_provinces[0]` of the node; foreign otherwise
  own     max_pow - prev of an entry (province + ship + flat extras, no propagated power), clipped at 0
Cached in $EU4_RESEARCH_CACHE/final_r10_emb_rows.pkl (list of dicts).
Run from backend/ with .venv/bin/python.
"""
import collections
import pickle
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402

TAG = re.compile(r"^[A-Z0-9]{2,4}$")
CACHE_FILE = common.CACHE / "final_r10_emb_rows.pkl"


def own(x):
    return max(0.0, x.get("max_pow", 0.0) - x.get("prev", 0.0)) if isinstance(x, dict) else 0.0


def build(force=False):
    if CACHE_FILE.exists() and not force:
        return pickle.loads(CACHE_FILE.read_bytes())
    rows = []
    for e in common.entries():
        sid = e["id"]
        if sid in ("U01", "U02"):   # copies of S80 / S79
            continue
        cs = common.block(e, "countries")
        ps = common.block(e, "provinces")
        ns = common.nodes(e)
        prov_node = {k: p["trade"] for k, p in ps.items() if isinstance(p, dict) and "trade" in p}
        for tag, c in cs.items():
            if not isinstance(c, dict):
                continue
            emb = c.get("trade_embargoed_by")
            if not emb:
                continue
            if not isinstance(emb, list):
                emb = [emb]
            home = prov_node.get("-%s" % c["trade_port"]) if "trade_port" in c else None
            recs = []
            for n in ns:
                v = n.get(tag)
                if not (isinstance(v, dict) and "max_demand" in v):
                    continue
                ents = {k: x for k, x in n.items() if TAG.match(k) and isinstance(x, dict)}
                away = ("total" in v) and not v.get("has_capital")
                top = (n.get("top_provinces") or [None])[0]
                recs.append(dict(node=n["definitions"], md=v["max_demand"] * (2.0 if away else 1.0), md_raw=v["max_demand"],
                                 away=away, dom=(n["definitions"] == home) or top == tag, ents=ents,
                                 nf={k: n.get(k) for k in ("max", "p_pow", "total", "highest_power", "retain_power")}))
            caps = {}
            for cls in (True, False):
                cl = [r["md"] for r in recs if r["dom"] == cls and not any(own(r["ents"].get(q)) > 0 for q in emb)]
                if cl:
                    caps[cls] = collections.Counter(round(x, 3) for x in cl).most_common(1)[0][0]
            for r in recs:
                cap = caps.get(r["dom"])
                if not cap:
                    continue
                rows.append(dict(save=sid, tag=tag, emb=emb, node=r["node"], cap=cap, md=r["md"], md_raw=r["md_raw"], away=r["away"],
                                 dom=r["dom"], ents=r["ents"], nf=r["nf"],
                                 merc={q: cs.get(q, {}).get("mercantilism") for q in emb},
                                 red=1 - r["md"] / cap))
    tmp = CACHE_FILE.with_suffix(".tmp")
    tmp.write_bytes(pickle.dumps(rows))
    tmp.replace(CACHE_FILE)
    return rows


if __name__ == "__main__":
    r = build(force=True)
    print(len(r), "rows,", len({x["save"] for x in r}), "saves with embargoes")
