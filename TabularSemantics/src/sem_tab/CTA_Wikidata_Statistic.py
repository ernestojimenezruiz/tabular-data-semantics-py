import json
gt_ancestor = json.load(open('/Users/jiahen/Data/TableAnnotate/SemTab_Challenge/SemTab20/wikidata_tables_v5/gt/cta_gt_ancestor.json'))
d_keys = list()
ancestorN = 0
ancestorMax = 0
num = 0
for key in gt_ancestor.keys():
    ancs = gt_ancestor[key]
    if len(ancs) > 0:
        num += 1
        max_d, ds = 0, list()
        for a in ancs:
            v = int(ancs[a])
            ds.append(v)
            if v > max_d:
                max_d = v
        if max_d > len(set(ds)):
            print(key)
            d_keys.append(key)
        ancestorMax += max_d
        ancestorN += len(ancs)
print('%d have ancestor/descendent, total gts: %d' % (num, len(gt_ancestor.keys())))
print('avg ancestor/descendent max depth: %f' % (ancestorMax/num))
print('avg ancestors/descenents #: %f' % (ancestorN/num))

print('special GTs: %d' % len(d_keys))
