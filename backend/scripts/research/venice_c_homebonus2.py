"""R01/R09: which steering merchants count towards transfer_home_bonus? Hypothesis: those in a node from which the home node (has_capital) is reachable downstream."""
import sys, collections
sys.path.insert(0,'.')
sys.path.insert(0,'scripts/research')
import venice_load as V, venice_c_lib as L
_n0=V.nodes(V.files()[0]); _names=[n['definitions'] for n in _n0]
OUT={n:[] for n in _names}
for i,n in enumerate(_n0):
    for inc in L.as_list(n.get('incoming')):
        if isinstance(inc,dict) and 'from' in inc: OUT[_names[int(inc['from'])-1]].append(_names[i])
def reach(src):
    seen=set(); st=[src]
    while st:
        x=st.pop()
        for y in OUT.get(x,[]):
            if y not in seen: seen.add(y); st.append(y)
    return seen
R={}
res=collections.Counter(); bad=[]
F=V.files()
for i,p in enumerate(F):
    if i==0: continue
    cs=V.load(p,'countries'); ns=V.nodes(p)
    steer=collections.defaultdict(list); home={}
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k):
                if e.get('has_capital'): home[k]=n['definitions']
                if e.get('has_trader') and 'type' in e: steer[k].append(n['definitions'])
    for t,c in cs.items():
        if not isinstance(c,dict) or 'transfer_home_bonus' not in c or t not in home: continue
        cnt=0
        for nd in steer[t]:
            if nd not in R: R[nd]=reach(nd)
            if home[t] in R[nd] : cnt+=1
        ok=abs(c['transfer_home_bonus']-0.1*cnt)<1e-6
        res[ok]+=1
        if not ok and len(bad)<10 and i==len(F)-1: bad.append((t,c['transfer_home_bonus'],steer[t],home[t],cnt))
print(res); print(bad)

print('--- compare rules on the same population (all saves after the start snapshot)')
cmp=collections.Counter(); ex=collections.defaultdict(list)
for i,p in enumerate(F):
    if i==0: continue
    cs=V.load(p,'countries'); ns=V.nodes(p)
    steer=collections.defaultdict(list); home={}
    for n in ns:
        for k,e in n.items():
            if isinstance(e,dict) and L.TAGLIKE(k):
                if e.get('has_capital'): home[k]=n['definitions']
                if e.get('has_trader') and 'type' in e: steer[k].append((n['definitions'],e.get('steer_power',0)))
    for t,c in cs.items():
        if not isinstance(c,dict) or 'transfer_home_bonus' not in c or t not in home or not steer[t]: continue
        f=round(c['transfer_home_bonus']/0.1)
        n_all=len(steer[t]); n_reach=sum(1 for nd,_ in steer[t] if home[t] in R.setdefault(nd,reach(nd)))
        n_reach_or_home=sum(1 for nd,_ in steer[t] if nd==home[t] or home[t] in R.setdefault(nd,reach(nd)))
        key=('all' if f==n_all else '', 'reach' if f==n_reach else '', 'reach|at home' if f==n_reach_or_home else '')
        cmp[key]+=1
        if key==('','',''): ex[t].append((p.stem[6:],f,steer[t],home[t]))
print(cmp)
for t,v in list(ex.items())[:6]: print(t,v[:1])
