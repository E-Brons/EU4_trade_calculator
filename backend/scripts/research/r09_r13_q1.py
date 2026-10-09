"""R09 Q1: power_fraction, potential, pull_power, max_demand, num_collectors_including_pirates over the corpus."""
import sys,re,collections,math
sys.path.insert(0,'scripts/research')
import common
from app.parsing.tradenodes import load_trade_graph
TAG=re.compile(r'^[A-Z0-9]{2,4}$')
g=load_trade_graph()
down={}
def reach(n):
    if n not in down:
        s=set()
        for t in g.outgoing(n): s.add(t); s|=reach(t)
        down[n]=s
    return down[n]
def fx(x): return math.trunc(x*1000+1e-9)/1000
st=collections.Counter(); ex=collections.defaultdict(list)
def bad(k,c):
    st[k+' FAIL']+=1
    if len(ex[k])<3: ex[k].append(c)
for e in common.entries():
    ns=common.nodes(e); nodeids=[n['definitions'] for n in ns]
    for n in ns:
        nid=n['definitions']
        es={t:v for t,v in n.items() if TAG.match(t) and isinstance(v,dict)}
        eff={t:v.get('val',0)-v.get('t_out',0)+v.get('t_in',0) for t,v in es.items()}
        # key set equality
        a={t for t,v in es.items() if 'power_fraction' in v}; b={t for t,v in es.items() if 'total' in v}; c={t for t,v in es.items() if 'money' in v}
        st['entries with power_fraction']+=len(a); st['pf set==total-key set==money set']+= (a==b==c); st['nodes']+=1
        if 'retain_power' in n:
            for t in a:
                st['power_fraction checks']+=1
                v=es[t]; r=n['retain_power']
                if abs(v['power_fraction']-fx(eff[t]/r))>1e-9: bad('power_fraction=fx(eff/retain)',(e['id'],nid,t,v['power_fraction'],eff[t],r))
        # potential
        for t,v in es.items():
            if 'potential' in v and 'total' in n:
                st['potential checks']+=1
                if abs(v['potential']-fx((v.get('t_out',0)-v.get('t_in',0))/n['total']))>1e-9: bad('potential=fx((t_out-t_in)/node.total)',(e['id'],nid,t,v['potential'],v.get('t_out'),v.get('t_in'),n['total']))
            st['entries with potential']+= 'potential' in v
            st['entries with potential and (t_in or t_out)']+= ('potential' in v and ('t_in' in v or 't_out' in v))
            st['entries with t_in/t_out']+= ('t_in' in v or 't_out' in v)
        # pull_power (R03 rule from project)
        if 'pull_power' in n:
            coll_nodes=collections.defaultdict(set)
            st['pull nodes']+=1
        # num_collectors
        if 'num_collectors' in n:
            nc=sum(1 for v in es.values() if 'total' in v)
            st['num_collectors==#entries with total key']+= (n['num_collectors']==nc); st['num_collectors nodes']+=1
            d=n['num_collectors_including_pirates']-n['num_collectors']
            st[f'incl_pirates - num_collectors = {d}']+=1
            if d==1 and abs(n['collector_power_including_pirates']-n['collector_power'])>0.0015: st['d=1 but power differs']+=1
            if d==1 and 'PIR' in es: st['d=1 and PIR entry present']+=1
            if d==0 and 'PIR' in es: st['d=0 and PIR entry present']+=1
        # max_demand
        for t,v in es.items():
            st['country entries']+=1
            st['entries with max_demand']+= ('max_demand' in v)
            st['max_demand only (stub)']+= (set(v)=={'max_demand'})
            st['max_demand==1.0']+= (v.get('max_demand')==1.0)
            st['entry without max_demand has other keys']+= ('max_demand' not in v)
            if 'max_demand' not in v: st['  keys when missing: '+','.join(sorted(v))[:60]]+=1
            if 'val' in v and 'max_pow' in v and 'max_demand' in v:
                st['val checks']+=1
                if abs(v['val']-fx(v['max_pow']*v['max_demand']))>1e-9: bad('val=fx(max_pow*max_demand)',(e['id'],nid,t,v['val'],v['max_pow'],v['max_demand']))
    # pull_power with R03 rule
    collect={}
    for n in ns:
        for t,v in n.items():
            if TAG.match(t) and isinstance(v,dict) and ('total' in v): collect.setdefault(t,set()).add(n['definitions'])
    for n in ns:
        if 'pull_power' not in n: continue
        nid=n['definitions']; pull=0.0
        for t,v in n.items():
            if not(TAG.match(t) and isinstance(v,dict)): continue
            ef=v.get('val',0)-v.get('t_out',0)+v.get('t_in',0)
            here='total' in v
            if ('type' in v and v.get('has_trader')) or (not here and (collect.get(t,set()) & reach(nid))): pull+=ef
        st['pull checks']+=1
        if abs(pull-n['pull_power'])>0.0105: bad('pull_power R03 rule',(e['id'],nid,round(pull,3),n['pull_power']))
for k in sorted(st): print(k, st[k])
print(dict(ex))
