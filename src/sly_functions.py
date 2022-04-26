import supervisely


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