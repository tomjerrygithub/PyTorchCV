#!/usr/bin/env python
#-*- coding:utf-8 -*-
# Author: Donny You(youansheng@gmail.com)
# Evaluation of coco.


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import argparse
import json

from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from utils.tools.configer import Configer
from utils.tools.logger import Logger as Log


class CocoEvaluator(object):
    def __init__(self, configer):
        self.configer = configer

    def relabel(self, json_dir, method='ssd'):
        submission_file = os.path.join(json_dir, 'person_instances_val2017_{}_results.json'.format(method))
        img_id_list = list()
        object_list = list()

        for json_file in os.listdir(json_dir):
            json_path = os.path.join(json_dir, json_file)
            shotname, extensions = os.path.splitext(json_file)
            shotname = shotname.rstrip().split('_')[-1]
            try:
                img_id = int(shotname)
            except ValueError:
                Log.info('Invalid Json file: {}'.format(json_file))
                continue

            img_id_list.append(img_id)
            with open(json_path, 'r') as json_stream:
                info_tree = json.load(json_stream)
                for object in info_tree['objects']:
                    object_dict = dict()
                    object_dict['image_id'] = img_id
                    object_dict['category_id'] = int(self.configer.get('details', 'coco_cat_seq')[object['label']])
                    object_dict['score'] = object['score']
                    object_dict['bbox'] = [object['bbox'][0], object['bbox'][1],
                                           object['bbox'][2] - object['bbox'][0],
                                           object['bbox'][3] - object['bbox'][1]]

                    object_list.append(object_dict)

        with open(submission_file, 'w') as write_stream:
            write_stream.write(json.dumps(object_list))

        Log.info('Evaluate {} images...'.format(len(img_id_list)))
        return submission_file, img_id_list

    def evaluate(self, pred_file, gt_file, img_ids):
        # Do Something.
        gt_coco = COCO(gt_file)
        res_coco = gt_coco.loadRes(pred_file)
        coco_eval = COCOeval(gt_coco, res_coco, 'bbox')
        coco_eval.params.imgIds = img_ids # res_coco.getImgIds()
        coco_eval.evaluate()
        coco_eval.accumulate()
        coco_eval.summarize()


if __name__ == "__main__":
    # Example:
    # python coco_evaluator.py --hypes ../../../../hypes/pose/coco/op_vgg19_coco_pose.json
    #                          --json_dir ../../../results/pose/coco/test_dir/coco/json/
    #                          --gt_file /home/donny/DataSet/MSCOCO/annotations/person_instances_val2017.json
    parser = argparse.ArgumentParser()
    parser.add_argument('--hypes_file', default=None, type=str,
                        dest='hypes_file', help='The hypes file of pose.')
    parser.add_argument('--gt_file', default=None, type=str,
                        dest='gt_file', help='The groundtruth annotations file of coco instances.')
    parser.add_argument('--json_dir', default=None, type=str,
                        dest='json_dir', help='The json dir of predict annotations.')
    args = parser.parse_args()

    coco_evaluator = CocoEvaluator(Configer(hypes_file=args.hypes_file))
    if args.gt_file is not None:
        pred_file, img_ids = coco_evaluator.relabel(args.json_dir)
        coco_evaluator.evaluate(pred_file, args.gt_file, img_ids)

    else:
        submission_file, _ = coco_evaluator.relabel(args.json_dir)
        Log.info('Submisson file path: {}'.format(submission_file))