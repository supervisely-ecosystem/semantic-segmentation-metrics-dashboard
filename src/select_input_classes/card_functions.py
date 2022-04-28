import time

import supervisely
import src.sly_globals as g

import src.select_input_classes.card_widgets as card_widgets


def convert_projects_to_semantic_segmentation_task(target_classes_names_list):
    progress_cb = card_widgets.select_classes_progress(message='GT project to Segmentation Task',
                                                       total=supervisely.Project(g.gt_project_dir,
                                                                                 supervisely.OpenMode.READ).total_items)

    supervisely.fs.clean_dir(g.gt_project_dir_converted)
    supervisely.Project.to_segmentation_task(src_project_dir=g.gt_project_dir,
                                             dst_project_dir=g.gt_project_dir_converted,
                                             target_classes=target_classes_names_list,
                                             progress_cb=progress_cb.update)

    progress_cb = card_widgets.select_classes_progress(message='PRED project to Segmentation Task',
                                                       total=supervisely.Project(g.pred_project_dir,
                                                                                 supervisely.OpenMode.READ).total_items)

    supervisely.fs.clean_dir(g.pred_project_dir_converted)
    supervisely.Project.to_segmentation_task(src_project_dir=g.pred_project_dir,
                                             dst_project_dir=g.pred_project_dir_converted,
                                             target_classes=target_classes_names_list,
                                             progress_cb=progress_cb.update)

    progress_cb.close()


