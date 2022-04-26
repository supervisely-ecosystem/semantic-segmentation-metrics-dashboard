import os
from datetime import time

import src.select_input_projects.card_widgets as card_widgets

import src.sly_globals as g
import supervisely
from supervisely.app import StateJson
from supervisely.app.widgets import ProjectSelector


def download_project(project_selector_widget: ProjectSelector, state: StateJson, project_dir):
    project_info = g.api.project.get_info_by_id(project_selector_widget.get_selected_project_id(state))
    pbar = card_widgets.download_projects_progress(message='downloading projects', total=project_info.items_count * 2)

    if os.path.exists(project_dir):
        supervisely.fs.clean_dir(project_dir)

    supervisely.download_project(g.api, project_info.id, project_dir, cache=g.file_cache,
                                 progress_cb=pbar.update, save_image_info=True)


def get_dataset_formatted_info(dataset_info: supervisely.Dataset = None):
    if dataset_info is not None:
        items_num = len(dataset_info.get_items_names())
        return {'name': dataset_info.name,
                'count': items_num}
    else:
        return {'name': '',
                'count': 0}


def get_datasets_statuses(gt_dataset_info: supervisely.Dataset, pred_dataset_info: supervisely.Dataset):
    gt_items_names, pred_items_names = set(gt_dataset_info.get_items_names()), \
                                       set(pred_dataset_info.get_items_names())

    # getting items intersection by names
    intersected_items_names = list(gt_items_names.intersection(pred_items_names))

    # getting items intersection by hashes
    matched_images_names: set = set()
    for item_name_from_intersected in intersected_items_names:
        gt_image_hash = gt_dataset_info.get_image_info(item_name_from_intersected).hash
        pred_image_hash = gt_dataset_info.get_image_info(item_name_from_intersected).hash

        if gt_image_hash == pred_image_hash:
            matched_images_names.add(item_name_from_intersected)

    gt_unique_images: set = gt_items_names.difference(matched_images_names)
    pred_unique_images: set = pred_items_names.difference(matched_images_names)

    return {
        'matched': len(matched_images_names),
        'gt_unique': len(gt_unique_images),
        'pred_unique': len(pred_unique_images)
    }


def get_datasets_table_content(gt_project_dir, pred_project_dir):
    def format_dataset_statuses(statuses_dict):
        formatted_statuses = {
            'numbers': [
                statuses_dict.get('matched', 0),
                statuses_dict.get('all_unmatched', 0),
                statuses_dict.get('gt_unique', 0),
                statuses_dict.get('pred_unique', 0),
                statuses_dict.get('gt_unmatched', 0),
                statuses_dict.get('pred_unmatched', 0),
            ],
            'colors': [
                '#008000FF',
                '#FF0000FF',
                '#20A0FFFF',
                '#20A0FFFF',
                '#FF0000FF',
                '#FF0000FF',
            ],
            'icons': [
                ["zmdi zmdi-check"],
                ["zmdi zmdi-close"],
                ["zmdi zmdi-long-arrow-left", "zmdi zmdi-plus-circle-o"],
                ["zmdi zmdi-plus-circle-o", "zmdi zmdi-long-arrow-right"],
                ["zmdi zmdi-close"],
                ["zmdi zmdi-close"],
            ],
            'messages': [
                'MATCHED',
                'UNMATCHED',
                'UNIQUE (GT)',
                'UNIQUE (PRED)',
                'UNMATCHED (GT)',
                'UNMATCHED (PRED)',
            ]
        }

        # filter None values
        # formatted_statuses = [x for x in formatted_statuses if x is not None]
        return formatted_statuses

    # reading projects
    gt_project = supervisely.Project(directory=gt_project_dir, mode=supervisely.OpenMode.READ)
    pred_project = supervisely.Project(directory=pred_project_dir, mode=supervisely.OpenMode.READ)

    # reading datasets
    gt_datasets = {key: value for key, value in zip(gt_project.datasets.keys(), gt_project.datasets.items())}
    pred_datasets = {key: value for key, value in zip(pred_project.datasets.keys(), pred_project.datasets.items())}

    table_content = []

    # fill table by datasets
    for gt_ds_name, gt_dataset_info in gt_datasets.items():
        row_in_table: dict = {}
        unformatted_statuses: dict = {}

        pred_dataset_info: supervisely.Dataset = pred_datasets.get(gt_ds_name)

        if pred_dataset_info is not None:  # if dataset exists on both sides
            row_in_table['left'] = get_dataset_formatted_info(gt_dataset_info)
            row_in_table['right'] = get_dataset_formatted_info(pred_dataset_info)

            unformatted_statuses.update(get_datasets_statuses(gt_dataset_info, pred_dataset_info))
            if unformatted_statuses['matched'] == 0:
                unformatted_statuses.update({'all_unmatched': -1})

        else:
            row_in_table['left'] = get_dataset_formatted_info(gt_dataset_info)
            row_in_table['right'] = get_dataset_formatted_info()
            unformatted_statuses.update({'pred_unmatched': -1})

        row_in_table['statuses'] = format_dataset_statuses(unformatted_statuses)

        table_content.append(row_in_table)

    return table_content

    # images_num in gt
    # images_num in pred

    # matched images
    # unique images
