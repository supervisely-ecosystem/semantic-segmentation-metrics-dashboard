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


def get_images_info(api: supervisely.Api, project_info):
    ds_info = {}
    ds_images = {}

    ws_to_team = {}
    for dataset in api.dataset.get_list(project_info.id):
        ds_info[dataset.name] = dataset
        images = api.image.get_list(dataset.id)
        modified_images = []
        for image_info in images:
            if project_info.workspace_id not in ws_to_team:
                ws_to_team[project_info.workspace_id] = api.workspace.get_info_by_id(project_info.workspace_id).team_id
            meta = {
                "team_id": ws_to_team[project_info.workspace_id],
                "workspace_id": project_info.workspace_id,
                "project_id": project_info.id,
                "project_name": project_info.name,
                "dataset_name": dataset.name,
                "meta": image_info.meta
            }
            image_info = image_info._replace(meta=meta)
            modified_images.append(image_info)
        ds_images[dataset.name] = modified_images
    return ds_info, ds_images



def get_table_content(gt_ds_info, gt_ds_images_info, pred_ds_info, pred_ds_images_info):
    ds_names = gt_ds_info.keys() | pred_ds_images_info.keys()

    results = []
    results_data = []
    for idx, name in enumerate(ds_names):
        compare = {"dsIndex": idx}
        images1 = gt_ds_images_info.get(name, [])
        images2 = pred_ds_info.get(name, [])
        if len(images1) == 0:
            compare["message"] = ["unmatched (in GT project)"]
            compare["icon"] = [["zmdi zmdi-long-arrow-left", "zmdi zmdi-alert-circle-o"]]

            compare["color"] = ["#F39C12"]
            compare["numbers"] = [-1]
            compare["left"] = {"name": ""}
            compare["right"] = {"name": name, "count": len(images2)}
            results_data.append([images2])
        elif len(images2) == 0:
            compare["message"] = ["unmatched (in PRED project)"]
            compare["icon"] = [["zmdi zmdi-alert-circle-o", "zmdi zmdi-long-arrow-right"]]
            compare["color"] = ["#F39C12"]
            compare["numbers"] = [-1]
            compare["left"] = {"name": name, "count": len(images1)}
            compare["right"] = {"name": ""}
            results_data.append([images1])
        else:
            img_dict1 = {img_info.name: img_info for img_info in images1}
            img_dict2 = {img_info.name: img_info for img_info in images2}

            matched = []
            diff = []  # same names but different hashes or image sizes
            same_names = img_dict1.keys() & img_dict2.keys()
            for img_name in same_names:
                dest = matched if img_dict1[img_name].hash == img_dict2[img_name].hash else diff
                dest.append([img_dict1[img_name], img_dict2[img_name]]) # extend

            uniq1 = [img_dict1[name] for name in img_dict1.keys() - same_names]
            uniq2 = [img_dict2[name] for name in img_dict2.keys() - same_names]

            compare["message"] = ["matched", "conflicts", "unique (left)", "unique (right)"]
            compare["icon"] = [["zmdi zmdi-check"], ["zmdi zmdi-close"], ["zmdi zmdi-plus-circle-o"],
                               ["zmdi zmdi-plus-circle-o"]]
            compare["color"] = ["green", "red", "#20a0ff", "#20a0ff"]
            compare["numbers"] = [len(matched), len(diff), len(uniq1), len(uniq2)]
            compare["left"] = {"name": name, "count": len(images1)}
            compare["right"] = {"name": name, "count": len(images2)}
            results_data.append([matched, diff, uniq1, uniq2])

        results.append(compare)

    # RESULTS = results
    # RESULTS_DATA = results_data
    return results


def some_load():
    # g.gt_project_info = g.api.project.get_info_by_id(, raise_error=True)
    # g._gt_meta_ = api.project.get_meta(state['gtProjectId'])
    # g.gt_meta = sly.ProjectMeta.from_json(g._gt_meta_)

    # g.pred_project_info = api.project.get_info_by_id(state['predProjectId'], raise_error=True)
    # g._pred_meta_ = api.project.get_meta(state['predProjectId'])
    # g.pred_meta = sly.ProjectMeta.from_json(g._pred_meta_)
    # intersected_meta = get_metas_intersection(gt_meta=, pred_meta=)

    gt_ds_info, gt_ds_images_info = get_images_info(api=g.api, project_info=)
    pred_ds_info, pred_ds_images_info = get_images_info(api=g.api, project_info=)

    table_content = get_table_content(gt_ds_info=gt_ds_info, gt_ds_images_info=gt_ds_images_info,
                                      pred_ds_info=pred_ds_info, pred_ds_images_info=pred_ds_images_info)

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



