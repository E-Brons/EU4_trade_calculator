"""R09 final: tiny check recorder shared by the final_r09_*.py scripts.
rec(check, sid, ok, info): counts over the 86 corpus entries ('all') and the 84 distinct saves ('dist', U01/U02 left out)."""
import collections, json

class Rec:
    def __init__(self):
        self.n = collections.Counter(); self.ok = collections.Counter()
        self.nd = collections.Counter(); self.okd = collections.Counter()
        self.ex = collections.defaultdict(list)
        self.order = []

    def rec(self, check, sid, ok, info=None, dup=False):
        if check not in self.order: self.order.append(check)
        self.n[check] += 1; self.ok[check] += bool(ok)
        if not dup:
            self.nd[check] += 1; self.okd[check] += bool(ok)
        if not ok:
            self.ex[check].append((sid,) + tuple(info if isinstance(info, (tuple, list)) else (info,)))

    def report(self, maxex=12, only=None):
        for c in self.order:
            if only and c not in only: continue
            bad = self.n[c] - self.ok[c]; badd = self.nd[c] - self.okd[c]
            print(f"{c:70s} dist {self.okd[c]:>8}/{self.nd[c]:<8} all86 {self.ok[c]:>8}/{self.n[c]:<8} fails(dist/all) {badd}/{bad}")
            for e in self.ex[c][:maxex]: print("      ", e)
            if len(self.ex[c]) > maxex:
                print(f"       ... {len(self.ex[c]) - maxex} more; grouped by the first field after the save id:")
                g = collections.defaultdict(list)
                for e in self.ex[c]: g[e[1] if len(e) > 1 else ""].append(e[0])
                for k, v in sorted(g.items(), key=lambda x: -len(x[1])): print(f"         {k}: {len(v)} saves {v if len(v) <= 12 else v[:4] + ['...'] + v[-2:]}")

    def dump(self, path):
        json.dump({"n": self.n, "ok": self.ok, "nd": self.nd, "okd": self.okd,
                   "ex": {k: v for k, v in self.ex.items()}}, open(path, "w"), default=str)
