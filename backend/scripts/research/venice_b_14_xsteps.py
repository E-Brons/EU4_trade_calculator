import sys, collections
sys.path.insert(0, 'scripts/research')
import venice_load as V

def xs(p):
    d = collections.defaultdict(list)
    for n in V.nodes(p):
        for c, e in n.items():
            if isinstance(e, dict) and c.isupper() and e.get('money') and e.get('total') and e['total'] > 0.1:
                d[c].append(e['money'] / e['total'])
    return {c: sum(v) / len(v) for c, v in d.items()}

def main():
  prev = None
  for p in V.files():
      cur = xs(p); tag = p.stem[6:]
      if prev:
          common = set(cur) & set(prev[1])
          steps = collections.Counter(round(cur[c] - prev[1][c], 2) for c in common if abs(cur[c] - prev[1][c]) > 0.004)
          print(prev[0], '->', tag, 'countries', len(common), 'steps(>0.004):', dict(sorted(steps.items())))
      prev = (tag, cur)


if __name__ == '__main__':
    main()
