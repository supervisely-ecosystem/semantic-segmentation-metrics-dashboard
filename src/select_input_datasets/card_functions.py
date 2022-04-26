from datetime import time

import src.select_input_projects.card_widgets as card_widgets

import src.sly_globals as g
import supervisely
from supervisely.app import StateJson, DataJson
from supervisely.app.widgets import ProjectSelector


def get_metas_intersection(gt_meta, pred_meta):
    aggregated_meta = {'classes': [], 'tags': [dict], 'projectType': 'images'}
    for i in gt_meta['classes']:
        for j in pred_meta['classes']:
            if i['title'] == j['title'] and i['shape'] == j['shape']:
                aggregated_meta['classes'].append(i)
    for i in gt_meta['tags']:
        aggregated_meta['tags'].append(i)

    tag_names = [i['name'] for i in aggregated_meta['tags']]
    for j in pred_meta['tags']:
        if j['name'] not in tag_names:
            aggregated_meta['tags'].append(j)

    return supervisely.ProjectMeta.from_json(aggregated_meta)

def some_load():
    # # g.gt_project_info = g.api.project.get_info_by_id(, raise_error=True)
    # # g._gt_meta_ = api.project.get_meta(state['gtProjectId'])
    # # g.gt_meta = sly.ProjectMeta.from_json(g._gt_meta_)
    #
    # # g.pred_project_info = api.project.get_info_by_id(state['predProjectId'], raise_error=True)
    # # g._pred_meta_ = api.project.get_meta(state['predProjectId'])
    # # g.pred_meta = sly.ProjectMeta.from_json(g._pred_meta_)
    # # intersected_meta = get_metas_intersection(gt_meta=, pred_meta=)
    #
    # gt_ds_info, gt_ds_images_info = get_images_info(api=g.api, project_info=)
    # pred_ds_info, pred_ds_images_info = get_images_info(api=g.api, project_info=)
    #
    # table_content = get_table_content(gt_ds_info=gt_ds_info, gt_ds_images_info=gt_ds_images_info,
    #                                   pred_ds_info=pred_ds_info, pred_ds_images_info=pred_ds_images_info)

    DataJson()['table_content'] = table_content
    DataJson().synchronize_changes()

    # intersected_keys = list(set(list(gt_ds_images_info)) & set(list(pred_ds_images_info)))
    #
    # images_dict = {}
    # for intersected_key in intersected_keys:
    #     images_dict['gt_images'][intersected_key] = []
    #     images_dict['pred_images'][intersected_key] = []
    #
    #     for gt_element in gt_ds_images_info[intersected_key]:
    #         for pred_element in pred_ds_images_info[intersected_key]:
    #             if gt_element.hash == pred_element.hash and gt_element.name == pred_element.name:
    #                 images_dict.setdefault('gt_images', {})[intersected_key].append(gt_element)
    #                 images_dict.setdefault('pred_images', {})[intersected_key].append(pred_element)



