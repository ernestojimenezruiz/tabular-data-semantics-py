import json
import os
from kg.endpoints import WikidataEndpoint

input_gt_file = '/Users/jiahen/Data/TableAnnotate/SemTab_Challenge/SemTab20/wikidata_tables_v5/gt/cta_gt.csv'
gt_extension_file = '/Users/jiahen/Data/TableAnnotate/SemTab_Challenge/SemTab20/wikidata_tables_v5/gt/cta_gt_descendent.json'
extension_type = 'descendent' # or descendent

gts = set()
with open(input_gt_file) as f:
    for line in f.readlines():
        gt = line.strip().split(',')[2]
        gts.add(gt)

ep = WikidataEndpoint()

if extension_type == 'ancestor':
    gt_sup2d = json.load(open(gt_extension_file)) if os.path.exists(gt_extension_file) else dict()
    for i, gt in enumerate(gts):
        if gt not in gt_sup2d:
            sup2dist = ep.getDistanceToAllSuperClasses(gt)
            sup_d = dict()
            for sup in sup2dist:
                d = list(sup2dist[sup])[0]
                sup_d[sup] = d
            gt_sup2d[gt] = sup_d
            if i % 100 == 0:
                print('%d done' % i)
                json.dump(gt_sup2d, open(gt_extension_file, 'w'))

    json.dump(gt_sup2d, open(gt_extension_file, 'w'))

elif extension_type == 'descendent':
    gt_sub2d = json.load(open(gt_extension_file)) if os.path.exists(gt_extension_file) else dict()
    for i, gt in enumerate(gts):
        if gt not in gt_sub2d:
            sub2dist = ep.getDistanceToAllSubClasses(uri_class=gt, max_level=3)
            sub_d = dict()
            for sub in sub2dist:
                d = list(sub2dist[sub])[0]
                sub_d[sub] = d
            gt_sub2d[gt] = sub_d
            if i % 100 == 0:
                print('%d done' % i)
                json.dump(gt_sub2d, open(gt_extension_file, 'w'))

    json.dump(gt_sub2d, open(gt_extension_file, 'w'))
