from datetime import time

import src.select_input_projects.card_widgets as card_widgets

import src.sly_functions as f
import src.sly_globals as g
import supervisely
from supervisely.app import StateJson, DataJson
from supervisely.app.widgets import ProjectSelector

#
# def get_metas_intersection(gt_meta, pred_meta):
#     aggregated_meta = {'classes': [], 'tags': [dict], 'projectType': 'images'}
#     for i in gt_meta['classes']:
#         for j in pred_meta['classes']:
#             if i['title'] == j['title'] and i['shape'] == j['shape']:
#                 aggregated_meta['classes'].append(i)
#     for i in gt_meta['tags']:
#         aggregated_meta['tags'].append(i)
#
#     tag_names = [i['name'] for i in aggregated_meta['tags']]
#     for j in pred_meta['tags']:
#         if j['name'] not in tag_names:
#             aggregated_meta['tags'].append(j)
#
#     return supervisely.ProjectMeta.from_json(aggregated_meta)


def get_classes_table_content(selected_datasets):
    # reading datasets

    project = supervisely.Project(directory=g.gt_project_dir, mode=supervisely.OpenMode.READ)
    project = supervisely.Project(directory=g.pred_project_dir, mode=supervisely.OpenMode.READ)







