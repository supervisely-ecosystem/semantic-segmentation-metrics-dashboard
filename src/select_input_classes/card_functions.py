import time

import supervisely
import src.sly_globals as g
import src.sly_functions as f

import src.select_input_classes.card_widgets as card_widgets
from supervisely.app import DataJson


def calculate_base_metrics(gt_project_dir, pred_project_dir):
    pixel_accuracy = []
    mean_iou = []

    ds_names = DataJson()['selected_datasets_names']
    cls_names = DataJson()['selected_classes_names']

    gt_project_meta = supervisely.Project(directory=gt_project_dir, mode=supervisely.OpenMode.READ).meta
    pred_project_meta = supervisely.Project(directory=pred_project_dir, mode=supervisely.OpenMode.READ).meta

    gt_datasets = f.get_datasets_dict_by_project_dir(gt_project_dir)
    pred_datasets = f.get_datasets_dict_by_project_dir(pred_project_dir)

    for ds_name in ds_names:
        gt_ds_info: supervisely.Dataset = gt_datasets[ds_name]
        pred_ds_info: supervisely.Dataset = pred_datasets[ds_name]

        images_names = g.ds2matched[ds_name]

        for image_name in images_names:
            gt_ann = gt_ds_info.get_ann(image_name, gt_project_meta)
            pred_ann = pred_ds_info.get_ann(image_name, pred_project_meta)





