import os

import supervisely

import src.sly_globals as g


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


def add_bg_object_to_image(dataset: supervisely.Dataset, item_name, pr_meta):
    img_info = dataset.get_image_info(item_name)
    annotation: supervisely.Annotation = dataset.get_ann(item_name, pr_meta)
    rectangle = supervisely.Rectangle.from_size(annotation.img_size)

    # [for annotation.labels]
    pass


def add_bg_object_to_all_images(project_dir):
    pr_meta = supervisely.Project(directory=project_dir, mode=supervisely.OpenMode.READ).meta
    if pr_meta.obj_classes.get(g.bg_class_name) is None:
        pr_meta = pr_meta.add_obj_class(supervisely.ObjClass(g.bg_class_name, supervisely.Bitmap, color=[0, 0, 0]))

    datasets = get_datasets_dict_by_project_dir(project_dir)

    dataset: supervisely.Dataset
    for ds_name, dataset in datasets.items():
        # items_names = ds_info.get_items_names()

        items_names = g.ds2matched[ds_name]

        for item_name in items_names:
            add_bg_object_to_image(dataset=dataset, item_name=item_name, pr_meta=pr_meta)


def convert_project_to_semantic_segmentation_task(src_project_dir, dst_project_dir=None,
                                                  target_classes_names_list=None, progress_cb=None):

    if dst_project_dir is not None and os.path.isdir(dst_project_dir):
        supervisely.fs.clean_dir(dst_project_dir)

    supervisely.Project.to_segmentation_task(src_project_dir=src_project_dir,
                                             dst_project_dir=dst_project_dir,
                                             target_classes=target_classes_names_list,
                                             progress_cb=progress_cb)
