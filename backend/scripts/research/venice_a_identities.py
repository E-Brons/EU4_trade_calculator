"""Venice series: node identities (I1-I7 of final_r12_identities.py) and link identities, per save, in integer thousandths.
Run from backend/:  python3 scripts/research/venice_a_identities.py"""
import sys
sys.path.insert(0, "scripts/research")
from collections import Counter, defaultdict
import final_r12_common as C
from final_r12_common import m3, lst, entries_of, OUT
import venice_load as V

def cdiv(a, b): return -((-a) // b)
def tdiv(a, b): return a // b if a >= 0 else -((-a) // b)

def check(nodes):
    N = Counter(); OK = Counter()
    def chk(name, ok):
        N[name] += 1; OK[name] += bool(ok)
    inc = C.incoming_links(nodes)
    insum = defaultdict(int)
    for (s, d), L in inc.items(): insum[d] += sum(v for v, a in L)
    for n in nodes:
        nid = n["definitions"]
        rp = m3(n.get("retain_power", 0)); pl = m3(n.get("pull_power", 0)); ret = m3(n["retention"])
        tot = rp + pl
        chk("I1 retention", ret == (1000 if tot == 0 else cdiv(rp * 1000, tot)))
        gross = m3(n.get("local_value", 0)) + insum[nid]
        cur = m3(n.get("current", 0)); out = m3(n.get("outgoing", 0))
        sw = sum(m3(x) for x in lst(n.get("steer_power")))
        if OUT[nid] and sw == 0: chk("I2b current=gross (links, sum w=0)", cur == gross)
        else: chk("I2a current=ceil3(gross*ret)", cur == cdiv(gross * ret, 1000))
        chk("I3 outgoing=gross-current", out == gross - cur)
        if "outgoing" in n: chk("I4 vao=outgoing", m3(n.get("value_added_outgoing")) == out)
        for tag, e in entries_of(n).items():
            if "max_pow" in e and "max_demand" in e and "val" in e:
                chk("I7 val=trunc3(max_pow*md)", m3(e["val"]) == tdiv(m3(e["max_pow"]) * m3(e["max_demand"]), 1000))
            if "power_fraction" in e and "val" in e:
                eff = m3(e["val"]) - m3(e.get("t_out", 0)) + m3(e.get("t_in", 0))
                chk("I5 pf=trunc3(eff/retain)", rp > 0 and m3(e["power_fraction"]) == tdiv(eff * 1000, rp))
                if "total" in e and "current" in n: chk("I6 total=trunc3(cur*pf)", m3(e["total"]) == tdiv(cur * m3(e["power_fraction"]), 1000))
    # link identities (R08 C-06)
    order = [n["definitions"] for n in nodes]
    for n in nodes:
        w = [m3(x) for x in lst(n.get("steer_power"))]; out = m3(n.get("outgoing", 0))
        for li, tgt in enumerate(OUT[n["definitions"]]):
            if li >= len(w): continue
            L = inc.get((n["definitions"], tgt))
            if not L: continue
            v, a = L[0]
            chk("L1 value-add within [out*w, out*(w+.001)]", out * w[li] // 1000 - 2 <= v - a <= (out * (w[li] + 1)) // 1000 + 2)
    return N, OK

if __name__ == "__main__":
    tot = Counter(); totn = Counter()
    for p in V.files():
        N, OK = check(V.nodes(p))
        bad = {k: f"{OK[k]}/{N[k]}" for k in N if OK[k] != N[k]}
        print(p.stem[6:], "all identities exact" if not bad else bad)
        tot.update(OK); totn.update(N)
    print({k: f"{tot[k]}/{totn[k]}" for k in totn})
