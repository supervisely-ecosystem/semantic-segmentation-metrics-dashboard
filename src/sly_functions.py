import os

import cv2
import numpy as np

import supervisely

import src.sly_globals as g
from supervisely.app import DataJson


def get_project_items_count(directory):
    return supervisely.Project(directory=directory, mode=supervisely.OpenMode.READ).total_items


def get_datasets_dict_by_project_dir(directory):
    project = supervisely.Project(directory=directory, mode=supervisely.OpenMode.READ)
    return {key: value for key, value in zip(project.datasets.keys(), project.datasets.items())}


def get_matched_and_unmatched_images_names(gt_dataset_info, pred_dataset_info):
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

    gt_unique_images_names: set = gt_items_names.difference(matched_images_names)
    pred_unique_images_names: set = pred_items_names.difference(matched_images_names)
    return {
        'matched_images_names': matched_images_names,
        'gt_unique_images_names': gt_unique_images_names,
        'pred_unique_images_names': pred_unique_images_names

    }


def convert_project_to_semantic_segmentation_task(src_project_dir, dst_project_dir=None,
                                                  target_classes_names_list=None, progress_cb=None):

    if dst_project_dir is not None and os.path.isdir(dst_project_dir):
        supervisely.fs.clean_dir(dst_project_dir)

    supervisely.Project.to_segmentation_task(src_project_dir=src_project_dir,
                                             dst_project_dir=dst_project_dir,
                                             target_classes=target_classes_names_list,
                                             progress_cb=progress_cb)


def get_mask_with_color_mask(annotation):
    # get mask with color mapping
    objname2color = {}
    mask = np.zeros([annotation.img_size[0], annotation.img_size[1], 3], dtype=np.uint8)
    for label in annotation.labels:
        label_color = label.obj_class.color

        label.geometry.draw(mask, label_color)
        objname2color[label.obj_class.name] = tuple(label_color)

    return mask, objname2color


def calculate_metrics_for_image(gt_ann: supervisely.Annotation, pred_ann: supervisely.Annotation, ds_name, item_name):
    g.pixels_matches.setdefault(ds_name, {}).setdefault(item_name, {})
    g.iou_scores.setdefault(ds_name, {}).setdefault(item_name, {})

    db_pixels_matches = g.pixels_matches[ds_name][item_name]
    db_iou_scores = g.iou_scores[ds_name][item_name]

    selected_classes_names = DataJson()['selected_classes_names']

    gt_mask, gt_color_mapping = get_mask_with_color_mask(gt_ann)
    pred_mask, pred_color_mapping = get_mask_with_color_mask(pred_ann)

    img_size = np.prod(gt_ann.img_size)

    for gt_class_name in selected_classes_names:
        db_pixels_matches.setdefault(gt_class_name, {})

        gt_color = gt_color_mapping.get(gt_class_name)

        for pred_class_name in selected_classes_names:
            pred_color = pred_color_mapping.get(pred_class_name)

            if gt_color is None and pred_color is None:        # if object is absent on GT && PRED masks (both)
                continue

            elif gt_color is not None and pred_color is None:  # if object appears on GT mask only
                db_pixels_matches[gt_class_name][pred_class_name] = 0
                if gt_class_name == pred_class_name:
                    db_iou_scores[gt_class_name] = 0
                continue

            elif gt_color is None and pred_color is not None:  # if object appears on PRED mask only
                db_pixels_matches[gt_class_name][pred_class_name] = 0
                if gt_class_name == pred_class_name:
                    db_iou_scores[gt_class_name] = 0
                continue

            else:                                              # if object appears on GT && PRED mask (both)
                gt_pixels_of_interest = gt_mask == gt_color_mapping[gt_class_name]
                pred_pixels_of_interest = pred_mask == pred_color_mapping[pred_class_name]

                masks_intersection = np.sum(np.logical_and(gt_pixels_of_interest, pred_pixels_of_interest)) // 3
                masks_union = np.sum(np.logical_or(gt_pixels_of_interest, pred_pixels_of_interest)) // 3

                intersection = masks_intersection / img_size
                db_pixels_matches[gt_class_name][pred_class_name] = intersection

                if gt_class_name == pred_class_name:
                    iou = masks_intersection / masks_union
                    db_iou_scores[gt_class_name] = iou


