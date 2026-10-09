"""Independent data for R08 Q2: the val-rank rule on the TUR/played saves (S79, S80, U03-U06) and the Venice saves, same test as venice_b_5."""
import sys
sys.path.insert(0, 'scripts/research')
import common, venice_b_5_rank as R
for e in common.entries():
    if e['id'] in ('S79', 'S80', 'U03', 'U04', 'U05', 'U06'):
        ns = common.nodes(e)
        ok, tot, bad = R.test(ns, 'val')
        print(e['id'], e['date'], ok, '/', tot, bad[:3])
