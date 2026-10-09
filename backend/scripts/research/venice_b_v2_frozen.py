"""SECOND PASS: order-insensitive raw comparison of the trade block between same-month saves: per node, the multiset of lines of each entry block; report which line keys differ."""
import sys, collections, re
sys.path.insert(0, 'scripts/research')
import venice_b_v2_raw as R
by = {p.stem[6:]: p for p in R.files()}
pairs = [('1444_11_11', '1444_11_14'), ('1444_11_14', '1444_11_30'), ('1444_12_01', '1444_12_02'), ('1444_12_02', '1444_12_11'), ('1444_12_11', '1444_12_31'),
         ('1445_01_01', '1445_01_02'), ('1445_01_02', '1445_01_15'), ('1445_01_15', '1445_01_24'), ('1445_01_24', '1445_01_30'), ('1445_01_30', '1445_01_31'),
         ('1445_02_01', '1445_02_03'), ('1445_02_03', '1445_02_10'), ('1445_02_10', '1445_02_17'), ('1445_02_17', '1445_02_28'), ('1445_03_01', '1445_03_31')]
tot = collections.Counter(); nodelevel = 0; order_only = 0
for a, b in pairs:
    na, nb = R.nodes(by[a]), R.nodes(by[b])
    for name in na:
        ea, sa, wa = na[name]; eb, sb, wb = nb[name]
        if wa != wb: nodelevel += 1          # node weights
        head_a = re.sub(r'\n\t\t[A-Z][A-Z0-9]{2}=\{.*', '', sa, flags=re.S)
        for tag in set(ea) | set(eb):
            da, db = ea.get(tag), eb.get(tag)
            if da is None or db is None: tot[('entry appears/disappears', 'max_demand-only' if (da or db) and list((da or db).keys()) == ['max_demand'] else 'other')] += 1; continue
            for k in set(da) | set(db):
                if da.get(k) != db.get(k): tot[k] += 1
        # node-level scalar lines before the first entry
        la = re.findall(r'\n\t\t(\w+)=([^\s{]+)', sa.split('\n\t\tPIR=')[0]); lb = re.findall(r'\n\t\t(\w+)=([^\s{]+)', sb.split('\n\t\tPIR=')[0])
        if la != lb: nodelevel += 1
print('node-level (scalars/weights before the first entry) differing nodes:', nodelevel)
print('entry-level key differences:', dict(tot))
