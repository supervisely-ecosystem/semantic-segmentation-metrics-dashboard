import os

import cv2
import torch
if torch.cuda.is_available():
    import cupy as np
else:
    import numpy as np

import supervisely

import src.sly_globals as g
from supervisely.app import DataJson


def get_project_items_count(directory):
    return supervisely.Project(directory=directory, mode=supervisely.OpenMode.READ).total_items


def get_datasets_dict_by_project_dir(directory):
    project = supervisely.Project(directory=directory, mode=supervisely.OpenMode.READ)
    return {key: value for key, value in zip(project.datasets.keys(), project.datasets.items())}


def get_project_items_count_by_class_names(directory):
    project_meta = supervisely.Project(directory=directory, mode=supervisely.OpenMode.READ).meta
    datasets_dict = get_datasets_dict_by_project_dir(directory)

    ds2counter = {ds: {} for ds in datasets_dict.keys()}

    dataset: supervisely.Dataset
    for dataset in datasets_dict.values():

        items_names = dataset.get_items_names()
        for item_name in items_names:
            ann = dataset.get_ann(item_name, project_meta)
            for label in ann.labels:
                ds2counter[dataset.name][label.obj_class.name] = ds2counter[dataset.name].get(label.obj_class.name, 0) + 1

    return ds2counter


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


def get_mask_with_colors_mapping(annotation):
    # get mask with color mapping
    objname2color = {}
    mask = np.zeros([annotation.img_size[0], annotation.img_size[1], 3], dtype=np.uint8)
    for label in annotation.labels:
        label_color = label.obj_class.color

        label.geometry.draw(mask, label_color)
        objname2color[label.obj_class.name] = tuple(label_color)

    return mask, objname2color


def get_size_of_gt_mask_union(gt_mask, pred_mask, gt_color, pred_color):
    if pred_color is not None:
        pred_interest = np.asarray(pred_mask == pred_color).all(-1)
    else:
        pred_interest = np.zeros(gt_mask.shape)

    if gt_color is not None:
        gt_interest = np.asarray(gt_mask == gt_color).all(-1)
    else:
        gt_interest = np.zeros(pred_mask.shape)

    return np.logical_or(pred_interest, gt_interest)


def get_gt_mask_class(gt_mask, gt_color):
    if gt_color is not None:
        gt_interest = np.asarray(gt_mask == gt_color).all(-1)
    else:
        gt_interest = np.zeros(gt_mask.shape)

    return gt_interest


def calculate_metrics_for_image(gt_ann: supervisely.Annotation, pred_ann: supervisely.Annotation, ds_name, item_name):
    g.pixels_matches.setdefault(ds_name, {}).setdefault(item_name, {})
    g.iou_scores.setdefault(ds_name, {}).setdefault(item_name, {})

    db_pixels_matches = g.pixels_matches[ds_name][item_name]
    db_iou_scores = g.iou_scores[ds_name][item_name]

    selected_classes_names = DataJson()['selected_classes_names']

    gt_mask, gt_color_mapping = get_mask_with_colors_mapping(gt_ann)
    pred_mask, pred_color_mapping = get_mask_with_colors_mapping(pred_ann)

    img_size = np.prod(gt_ann.img_size[:2])
    image_intersected_pixels_num = 0

    for gt_class_name in selected_classes_names:
        # class_union_mask = get_size_of_gt_mask_union(gt_mask, pred_mask, gt_color_mapping.get(gt_class_name), pred_color_mapping.get(gt_class_name))
        class_union_mask = get_gt_mask_class(gt_mask, gt_color_mapping.get(gt_class_name))
        if np.sum(class_union_mask) == 0:  # class not exists on both pixels
            continue

        db_pixels_matches.setdefault(gt_class_name, {})

        gt_color = gt_color_mapping.get(gt_class_name)
        for pred_class_name in selected_classes_names:
            pred_color = pred_color_mapping.get(pred_class_name)

            if gt_color is None and pred_color is None:  # if object is absent on GT && PRED masks (both)
                continue

            elif gt_color is not None and pred_color is None:  # if object appears on GT mask only
                db_pixels_matches[gt_class_name][pred_class_name] = 0
                if gt_class_name == pred_class_name:
                    db_iou_scores[gt_class_name] = 0
                    db_pixels_matches[gt_class_name][pred_class_name] = 0
                continue

            elif gt_color is None and pred_color is not None:  # if object appears on PRED mask only
                db_pixels_matches[gt_class_name][pred_class_name] = 0
                if gt_class_name == pred_class_name:
                    db_iou_scores[gt_class_name] = 0
                continue

            else:  # if object appears on GT && PRED mask (both)
                gt_pixels_of_interest = np.asarray(gt_mask == gt_color_mapping[gt_class_name]).all(-1)
                pred_pixels_of_interest = np.asarray(pred_mask == pred_color_mapping[pred_class_name]).all(-1)

                matched_mask = np.logical_and(pred_pixels_of_interest, class_union_mask)
                db_pixels_matches[gt_class_name][pred_class_name] = np.sum(matched_mask) / np.sum(class_union_mask)

                if gt_class_name == pred_class_name:
                    masks_intersection = np.logical_and(gt_pixels_of_interest, pred_pixels_of_interest)
                    masks_union = np.logical_or(gt_pixels_of_interest, pred_pixels_of_interest)

                    iou = np.sum(masks_intersection) / np.sum(masks_union)
                    db_iou_scores[gt_class_name] = iou

                    image_intersected_pixels_num += np.sum(masks_intersection)

    g.images_accuracy.setdefault(ds_name, {})[item_name] = image_intersected_pixels_num / img_size


def get_image_link(project_dir, ds_name, item_name):
    datasets_dict = get_datasets_dict_by_project_dir(project_dir)
    dataset: supervisely.Dataset = datasets_dict[ds_name]

    return dataset.get_image_info(item_name).path_original


def get_image_annotation(project_dir, ds_name, item_name):
    project_meta = supervisely.Project(directory=project_dir, mode=supervisely.OpenMode.READ).meta
    datasets_dict = get_datasets_dict_by_project_dir(project_dir)
    dataset: supervisely.Dataset = datasets_dict[ds_name]

    return dataset.get_ann(item_name, project_meta)


def filter_annotation_by_selected_classes(ann: supervisely.Annotation, selected_classes):
    filtered_labels = []
    for label in ann.labels:
        if label.obj_class.name in selected_classes:
            filtered_labels.append(label)

    return ann.clone(labels=filtered_labels)
