import sys; sys.path.insert(0,'/tmp/eu4research/repo/backend/scripts/research')
import common
i = int(sys.argv[1]); n = int(sys.argv[2])
for k, e in enumerate(common.entries()):
    if k % n == i:
        common.block(e, 'countries')
