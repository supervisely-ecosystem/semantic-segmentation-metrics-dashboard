import colorsys

import numpy as np
import pandas as pd

import supervisely
import src.sly_globals as g
import src.sly_functions as f

from supervisely.app import DataJson


def get_pixel_accuracy_for_image(image_stats):
    current_image_score = 0  # from 0 to 1

    for current_class_name, current_class_matches in image_stats.items():
        class_score = current_class_matches.get(current_class_name)

        if class_score is not None:
            current_image_score += class_score

    return current_image_score


def calculate_general_pixel_accuracy():
    # calculating Pixels Accuracy

    mean_between_images_accuracy = []
    for matched_images_in_dataset in g.pixels_matches.values():
        for current_image in matched_images_in_dataset.values():
            current_image_score = get_pixel_accuracy_for_image(image_stats=current_image)
            mean_between_images_accuracy.append(current_image_score)

    return sum(mean_between_images_accuracy) / len(mean_between_images_accuracy)  # mean by project


def calculate_general_mean_iou():
    # calculating mean Intersection over Union

    mean_iou = []

    for scores_by_images_in_dataset in g.iou_scores.values():
        for current_image_scores in scores_by_images_in_dataset.values():
            scores = list(current_image_scores.values())
            mean_iou.append(sum(scores) / len(scores))  # mean by image

    return sum(mean_iou) / len(mean_iou)  # mean by project


def get_matched_pixels_matrix_for_image(current_image, classes_names):
    data = [[] for _ in classes_names]

    for row_index, current_class_name in enumerate(classes_names):
        row = {class_name: 0 for class_name in classes_names}

        current_class_matches = current_image.get(current_class_name)

        if current_class_matches is not None:  # if not None — class exists on both of gt and pred images
            for match_name, match_score in current_class_matches.items():
                row[match_name] += match_score

            sum_of_row = sum(list(row.values()))
            row = [row[class_name] / sum_of_row for class_name in classes_names]
            data[row_index] = row
        else:
            data[row_index] = []

    return data


def get_matches_pixels_matrix_content():
    classes_names = DataJson()['selected_classes_names']

    data = []
    for matches_per_image in g.pixels_matches.values():  # collect matches for each image
        for current_image in matches_per_image.values():
            data.append(get_matched_pixels_matrix_for_image(current_image, classes_names))

    filtered_data = [[] for _ in classes_names]
    for matrix_for_image in data:  # filter unexciting classes
        for class_name_index, row in enumerate(matrix_for_image):
            if len(row) > 0:
                filtered_data[class_name_index].append(row)

    existing_class_names = []
    existing_class_matrix = []  # calculate mean values by existing rows

    columns_indexes_to_remove = []
    for class_name_index, class_name_data in enumerate(filtered_data):
        if len(class_name_data) > 0:
            existing_class_matrix.append(np.sum(class_name_data, axis=0) / len(class_name_data))
            existing_class_names.append(classes_names[class_name_index])
        else:
            columns_indexes_to_remove.append(class_name_index)

    existing_class_matrix = np.asarray(existing_class_matrix)
    existing_class_matrix = np.delete(existing_class_matrix, columns_indexes_to_remove, axis=1)

    # data = np.sum(data, axis=0) / len(data)

    return pd.DataFrame(data=existing_class_matrix, columns=existing_class_names)


def get_metric_color(metric_value):
    hue = metric_value * 120 / 360
    rgb = np.asarray(colorsys.hsv_to_rgb(hue, 1, 200))
    return f'rgb({int(rgb[0])},{int(rgb[1])},{int(rgb[2])})'


def colorize_metrics():
    acc_score = DataJson()['general_metrics']['accuracy']['value']
    iou_score = DataJson()['general_metrics']['iou']['value']

    DataJson()['general_metrics']['accuracy']['color'] = get_metric_color(acc_score)
    DataJson()['general_metrics']['iou']['color'] = get_metric_color(iou_score)

    DataJson()['general_metrics']['border_color'] = get_metric_color((acc_score + iou_score) / 2)


def update_class_items_stats_for_project(project_dir, stats_by_class_names, stats_by_datasets, flag):
    project_items_counts = f.get_project_items_count_by_class_names(project_dir)

    for ds_name, ds_counts in project_items_counts.items():
        for class_name, class_counts in ds_counts.items():
            class_stats = stats_by_class_names.get(class_name)
            if class_stats is not None:
                class_stats[flag] += class_counts


def get_stats_tables_content():
    classes_names = DataJson()['selected_classes_names']

    stats_by_class_names = {class_name: {
        'accuracy': [],
        'mean iou': [],
        'gt images num': 0,
        'pred images num': 0,
        'matched': 0
    } for class_name in classes_names}

    stats_by_datasets = {ds_name: {
        'accuracy': '-',
        'mean iou': '-',
        'matched': 0
    } for ds_name in g.pixels_matches.keys()}

    # collecting accuracy
    for ds_name, matched_images_in_dataset in g.pixels_matches.items():

        # per classes
        matched_pixels_by_classes_in_dataset = {class_name: [] for class_name in classes_names}
        for current_image in matched_images_in_dataset.values():
            matches_matrix = get_matched_pixels_matrix_for_image(current_image, classes_names)
            for class_name_index, row in enumerate(matches_matrix):
                if len(row) > 0:
                    match_score_on_image = row[class_name_index]
                    current_class_stats = matched_pixels_by_classes_in_dataset[classes_names[class_name_index]]
                    current_class_stats.append(match_score_on_image)

                    if match_score_on_image > 0:
                        stats_by_class_names[classes_names[class_name_index]]['matched'] += 1

        classname2matched = {class_name: sum(scores_list) / len(scores_list) for class_name, scores_list in
                             matched_pixels_by_classes_in_dataset.items() if len(scores_list) > 0}

        for class_name, class_score in classname2matched.items():
            stats_by_class_names[class_name]['accuracy'].append(class_score)

        # per datasets
        if len(classname2matched.values()) > 0:
            stats_by_datasets[ds_name]['accuracy'] = sum(classname2matched.values()) / len(classname2matched.values())
            stats_by_datasets[ds_name]['matched'] = len(matched_images_in_dataset)

    # collecting iou
    for ds_name, scores_by_images_in_dataset in g.iou_scores.items():

        # per classes
        scores_by_classes_in_dataset = {class_name: [] for class_name in classes_names}

        for current_image in scores_by_images_in_dataset.values():
            for class_name_on_image, class_score in current_image.items():
                scores_by_classes_in_dataset[class_name_on_image].append(class_score)

        classname2score = {class_name: sum(scores_list) / len(scores_list) for class_name, scores_list in
                           scores_by_classes_in_dataset.items() if len(scores_list) > 0}

        for class_name, class_score in classname2score.items():
            stats_by_class_names[class_name]['mean iou'].append(class_score)

        # per datasets
        if len(classname2score.values()) > 0:
            stats_by_datasets[ds_name]['mean iou'] = sum(classname2score.values()) / len(classname2score.values())

    # collecting images nums
    update_class_items_stats_for_project(g.gt_project_dir_converted, stats_by_class_names, stats_by_datasets,
                                         flag='gt images num')
    update_class_items_stats_for_project(g.gt_project_dir_converted, stats_by_class_names, stats_by_datasets,
                                         flag='pred images num')

    # scores lists to values
    for class_name in stats_by_class_names.keys():
        for score_key in ['accuracy', 'mean iou']:
            if len(stats_by_class_names[class_name][score_key]) > 0:
                stats_by_class_names[class_name][score_key] = \
                    sum(stats_by_class_names[class_name][score_key]) / len(stats_by_class_names[class_name][score_key])
            else:
                stats_by_class_names[class_name][score_key] = '-'

    # format tables
    stats_by_class_name_columns = ['class_name']  # classes stats table
    stats_by_class_name_columns.extend(list(stats_by_class_names[classes_names[0]].keys()))

    stats_by_class_name_data = []
    for class_name, class_stats in stats_by_class_names.items():
        row = [class_name]
        row.extend(list(class_stats.values()))
        stats_by_class_name_data.append(row)

    stats_by_datasets_columns = ['ds_name']  # ds stats table
    stats_by_datasets_columns.extend(list(list(stats_by_datasets.values())[0].keys()))

    stats_by_datasets_data = []
    for ds_name, ds_stats in stats_by_datasets.items():
        row = [ds_name]
        row.extend(list(ds_stats.values()))
        stats_by_datasets_data.append(row)

    return {'classes': pd.DataFrame(data=stats_by_class_name_data, columns=stats_by_class_name_columns),
            'datasets': pd.DataFrame(data=stats_by_datasets_data, columns=stats_by_datasets_columns)}


def get_images_table_content():
    selected_classes_names = DataJson()['selected_classes_names']
    table_content = []

    gt_datasets = f.get_datasets_dict_by_project_dir(g.gt_project_dir)
    pred_datasets = f.get_datasets_dict_by_project_dir(g.gt_project_dir)

    for ds_name, matched_items_names in g.ds2matched.items():
        gt_dataset: supervisely.Dataset = gt_datasets[ds_name]
        pred_dataset: supervisely.Dataset = pred_datasets[ds_name]

        for item_name in matched_items_names:
            pixels_matches = g.pixels_matches.get(ds_name, {}).get(item_name)
            if pixels_matches is not None:
                accuracy = get_pixel_accuracy_for_image(image_stats=pixels_matches)
            else:
                accuracy = '-'

            iou_scores = g.iou_scores.get(ds_name, {}).get(item_name)
            scores_per_class = {class_name: '-' for class_name in selected_classes_names}

            if iou_scores is not None:
                mean_iou = sum(list(iou_scores.values())) / len(iou_scores)
                scores_per_class.update(iou_scores)
            else:
                mean_iou = '-'

            gt_image_url = g.api.image.url(team_id=g.TEAM_ID,
                                           workspace_id=g.gt_project['workspace_id'],
                                           project_id=g.gt_project['project_id'],
                                           dataset_id=g.gt_ds2info[ds_name].id,
                                           image_id=gt_dataset.get_image_info(item_name).id)

            pred_image_url = g.api.image.url(team_id=g.TEAM_ID,
                                             workspace_id=g.pred_project['workspace_id'],
                                             project_id=g.pred_project['project_id'],
                                             dataset_id=g.pred_ds2info[ds_name].id,
                                             image_id=pred_dataset.get_image_info(item_name).id)

            table_content.append({
                'ds name': ds_name,
                'gt image': gt_image_url,
                'pred image': pred_image_url,
                'accuracy': accuracy,
                'mean IoU': mean_iou,
                **iou_scores
            })

    # table_content.update(iou_by_classes)
    return table_content
