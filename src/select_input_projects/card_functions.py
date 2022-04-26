import os
from datetime import time

import supervisely
from supervisely.app import StateJson
from supervisely.app.widgets import ProjectSelector

import src.select_input_projects.card_widgets as card_widgets

import src.sly_functions as f
import src.sly_globals as g


def download_project(project_selector_widget: ProjectSelector, state: StateJson, project_dir):
    project_info = g.api.project.get_info_by_id(project_selector_widget.get_selected_project_id(state))
    pbar = card_widgets.download_projects_progress(message='downloading projects', total=project_info.items_count * 2)

    if os.path.exists(project_dir):
        supervisely.fs.clean_dir(project_dir)

    supervisely.download_project(g.api, project_info.id, project_dir, cache=g.file_cache,
                                 progress_cb=pbar.update, save_image_info=True)


######################################
# @TODO: move to DatasetsCompare widget
######################################

def get_dataset_formatted_info(dataset_info: supervisely.Dataset = None):
    if dataset_info is not None:
        items_num = len(dataset_info.get_items_names())
        return {'name': dataset_info.name,
                'count': items_num}
    else:
        return {'name': '',
                'count': 0}


def get_datasets_statuses(gt_dataset_info: supervisely.Dataset, pred_dataset_info: supervisely.Dataset):
    matched_and_unmatched_images_names = f.get_matched_and_unmatched_images_names(gt_dataset_info, pred_dataset_info)

    return {
        'matched': len(matched_and_unmatched_images_names['matched_images_names']),
        'gt_unique': len(matched_and_unmatched_images_names['gt_unique_images_names']),
        'pred_unique': len(matched_and_unmatched_images_names['pred_unique_images_names'])
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
        return formatted_statuses

    # reading datasets
    gt_datasets = f.get_datasets_dict_by_project_dir(directory=gt_project_dir)
    pred_datasets = f.get_datasets_dict_by_project_dir(directory=pred_project_dir)

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

    # don't forget about right unique side
    for pred_ds_name, pred_dataset_info in pred_datasets.items():

        if gt_datasets.get(pred_ds_name) is None:
            row_in_table = {
                'left': get_dataset_formatted_info(),
                'right': get_dataset_formatted_info(pred_dataset_info),
                'statuses': format_dataset_statuses({'gt_unmatched': -1})
            }
            table_content.append(row_in_table)

    return table_content

######################################
# @TODO: move to ProjectsCompare widget
######################################
