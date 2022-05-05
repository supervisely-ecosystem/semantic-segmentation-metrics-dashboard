import time

import numpy as np

import supervisely
import src.sly_globals as g
import src.sly_functions as f

import src.select_input_classes.card_widgets as card_widgets
from supervisely.app import DataJson


def calculate_scores_tables(gt_project_dir, pred_project_dir):
    ds_names = DataJson()['selected_datasets_names']

    gt_project_meta = supervisely.Project(directory=gt_project_dir, mode=supervisely.OpenMode.READ).meta
    pred_project_meta = supervisely.Project(directory=pred_project_dir, mode=supervisely.OpenMode.READ).meta

    gt_datasets = f.get_datasets_dict_by_project_dir(gt_project_dir)
    pred_datasets = f.get_datasets_dict_by_project_dir(pred_project_dir)

    items_num = sum([len(images_set) for images_set in g.ds2matched.values()])

    with card_widgets.select_classes_progress(message='calculating metrics', total=items_num) as pbar:
        for ds_name in ds_names:
            gt_ds_info: supervisely.Dataset = gt_datasets[ds_name]
            pred_ds_info: supervisely.Dataset = pred_datasets[ds_name]

            images_names = g.ds2matched[ds_name]

            for image_name in images_names:
                gt_ann = gt_ds_info.get_ann(image_name, gt_project_meta)
                pred_ann = pred_ds_info.get_ann(image_name, pred_project_meta)

                f.calculate_metrics_for_image(gt_ann, pred_ann, ds_name, image_name)

                pbar.update()


def apply_classes_to_projects(selected_classes_names):
    with card_widgets.select_classes_progress(message='applying classes to GT',
                                              total=f.get_project_items_count(g.gt_project_dir)) as pbar:
        f.convert_project_to_semantic_segmentation_task(target_classes_names_list=selected_classes_names,
                                                        src_project_dir=g.gt_project_dir,
                                                        dst_project_dir=g.gt_project_dir_converted,
                                                        progress_cb=pbar.update)

    with card_widgets.select_classes_progress(message='applying classes to PRED',
                                              total=f.get_project_items_count(g.pred_project_dir)) as pbar:
        f.convert_project_to_semantic_segmentation_task(target_classes_names_list=selected_classes_names,
                                                        src_project_dir=g.pred_project_dir,
                                                        dst_project_dir=g.pred_project_dir_converted,
                                                        progress_cb=pbar.update)



