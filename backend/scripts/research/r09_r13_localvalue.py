"""R13 Q1: local_value == sum(size_g * base_price_g) / 12 with the goal's base prices; index->goods fitted in r09_r13_goods.py."""
import pickle, collections, json
C='/tmp/eu4research/cache/'
def al(x): return x if isinstance(x,list) else [x]
IDX=['unknown0','grain','wine','wool','cloth','fish','fur','salt','naval_supplies','copper','gold','iron','slaves','ivory','tea','chinaware','spices','coffee','cotton','sugar','tobacco','cocoa','silk','dyes','tropical_wood','livestock','incense','glass','paper','gems','idx30','cloves','idx32']
P={'grain':2.5,'wine':2.5,'wool':2.5,'fish':2.5,'cloth':3,'salt':3,'copper':3,'iron':3,'chinaware':3,'spices':3,'coffee':3,'cotton':3,'sugar':3,'tobacco':3,'glass':3,
   'fur':2,'naval_supplies':2,'slaves':2,'tea':2,'ivory':4,'cocoa':4,'silk':4,'dyes':4,'gems':4,'cloves':8,'coal':10,'paper':3.5,'incense':2.75,'gold':0,'tropical_wood':2,'livestock':2}
man=json.load(open('/Users/elkanabronstein/myProjects/EU4_Trade_calculator/backend/tests/fixtures/saves/saves.json'))['saves']
print('save, nodes, max|local_value - sum/12|, nodes off >0.002')
tot=0; off=0
for e in man:
    sid=e['id']; tr=pickle.load(open(f'{C}trade_{sid}.pkl','rb'))
    mx=0; bad=0; n_=0; worst=None
    for n in al(tr['node']):
        if not (isinstance(n,dict) and 'trade_goods_size' in n and 'local_value' in n): continue
        sz=al(n['trade_goods_size']); pred=sum(s*P.get(IDX[i],0) for i,s in enumerate(sz))/12
        d=abs(pred-n['local_value']); n_+=1
        if d>mx: mx=d; worst=(n['definitions'],n['local_value'],round(pred,3))
        bad+= d>0.002
    tot+=n_; off+=bad
    print(sid,n_,round(mx,4),bad,worst if bad else '')
print('TOTAL nodes',tot,'off',off)

# prices in later saves: per-save lstsq fit (price*12), goods that changed vs base table
import numpy as np
print('\nper-save fitted price*12 that differ from base table by >0.02')
for e in man:
    sid=e['id']
    if sid in ('S01','S14') or True:
        tr=pickle.load(open(f'{C}trade_{sid}.pkl','rb'))
        ns=[n for n in al(tr['node']) if isinstance(n,dict) and 'trade_goods_size' in n and 'local_value' in n]
        X=np.array([al(n['trade_goods_size']) for n in ns]); y=np.array([n['local_value'] for n in ns])*12
        used=[i for i in range(33) if X[:,i].any()]
        coef=np.linalg.lstsq(X[:,used],y,rcond=None)[0]
        diff={IDX[i]:(round(float(c),3),P.get(IDX[i])) for i,c in zip(used,coef) if abs(c-P.get(IDX[i],0))>0.05}
        if sid in ('S01','S14','S36','S37','S42','S64','S79','S80') or not diff: print(sid, diff if diff else 'all fitted prices == base table')
