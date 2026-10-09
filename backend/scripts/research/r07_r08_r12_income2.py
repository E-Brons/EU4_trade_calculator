import sys, math; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
from r07_r08_r12_income import *
def fx(x): return math.trunc(x*1000+1e-9)/1000
# Rules: bonus(node entry, home entry) in absolute efficiency terms
RULES={
 'M: +.1 if has_trader (any node)': lambda x,h: 0.1 if x.get('has_trader') else 0.0,
 'N: +.1 if has_trader, away, home has no merchant': lambda x,h: 0.1 if (x.get('has_trader') and not x.get('has_capital') and not h.get('has_trader')) else 0.0,
 'A: +.1 if has_trader and away': lambda x,h: 0.1 if (x.get('has_trader') and not x.get('has_capital')) else 0.0,
 'Z: never': lambda x,h: 0.0,
}
def run():
    pairs=defaultdict(list)
    for e,n,t,x in rows(): pairs[(e['id'],t)].append((n['id'],x))
    res=defaultdict(Counter)
    for (sid,t),L in pairs.items():
        home=[x for nid,x in L if x.get('has_capital')]
        if len(home)!=1: continue
        h=home[0]
        for name,rule in RULES.items():
            # country-level X0 from the home entry under this rule: money = fx(total*(1+X0+bonus_home))
            lo,hi=xint(f(h['money']),f(h['total']))
            b=rule(h,h); 
            for nid,x in L:
                if x is h: continue
                pred_lo=fx(f(x['total'])*(1+lo-b+rule(x,h))); 
                # allow interval: X0 in [lo-b, hi-b]
                pred_hi=fx(f(x['total'])*(1+hi-b+rule(x,h)))+0.001
                ok=pred_lo-0.0011<=f(x['money'])<=pred_hi+0.0011
                res[name][(('home_merch' if h.get('has_trader') else 'home_nomerch'),ok)]+=1
    return res
if __name__=='__main__':
    for k,v in run().items(): print(k, dict(v))
