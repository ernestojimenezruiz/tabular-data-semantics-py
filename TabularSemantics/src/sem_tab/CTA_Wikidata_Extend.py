import json
from kg.endpoints import WikidataEndpoint

input_gt_file = '/Users/jiahen/Data/TableAnnotate/SemTab_Challenge/SemTab20/wikidata_output_sample_v0/gt/cta_gt.csv'
gt_extension_file = '/Users/jiahen/Data/TableAnnotate/SemTab_Challenge/SemTab20/wikidata_output_sample_v0/gt/cta_gt_extension.json'

gts = list()
with open(input_gt_file) as f:
    for line in f.readlines():
        gt = line.strip().split(',')[2]
        gts.append(gt)

ep = WikidataEndpoint()

gt_sup2d = dict()
for i, gt in enumerate(gts):
    sup2dist = ep.getDistanceToAllSuperClasses(gt)
    sup_d = dict()
    for sup in sup2dist:
        d = list(sup2dist[sup])[0]
        sup_d[sup] = d
    gt_sup2d[gt] = sup_d
    if i % 10 == 0:
        print('%d done' % i)

json.dump(gt_sup2d, open(gt_extension_file, 'w'))
