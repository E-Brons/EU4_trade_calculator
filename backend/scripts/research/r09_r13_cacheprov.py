import sys
sys.path.insert(0,'scripts/research')
import common
from multiprocessing import Pool
def f(e):
    common.block(e,'provinces'); return e['id']
if __name__=='__main__':
    with Pool(4) as p:
        for i in p.imap_unordered(f, common.entries()): print(i, flush=True)
