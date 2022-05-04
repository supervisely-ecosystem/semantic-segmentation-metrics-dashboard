import colorsys

import numpy as np
import pandas as pd

import supervisely
import src.sly_globals as g
from src.segmentation_metrics_dashboard import card_widgets
from supervisely.app import DataJson


def calculate_general_pixel_accuracy():
    # calculating Pixels Accuracy

    mean_between_images_accuracy = []
    for matched_images_in_dataset in g.pixels_matches.values():
        for current_image in matched_images_in_dataset.values():
            current_image_score = 0  # from 0 to 1

            for current_class_name, current_class_matches in current_image.items():
                class_score = current_class_matches.get(current_class_name)

                if class_score is not None:
                    current_image_score += class_score

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
    for matrix_for_image in data:                        # filter unexciting classes
        for class_name_index, row in enumerate(matrix_for_image):
            if len(row) > 0:
                filtered_data[class_name_index].append(row)

    existing_class_names = []
    existing_class_matrix = []                           # calculate mean values by existing rows

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


def get_stats_by_classes_table_content():
    classes_names = DataJson()['selected_classes_names']

    stats_by_class_names = {}
    stats_by_datasets = {}

    for ds_name, matched_images_in_dataset in g.pixels_matches.items():
        stats_by_datasets.setdefault(ds_name, {})

        for current_image in matched_images_in_dataset.values():
            matches_per_images = get_matched_pixels_matrix_for_image(current_image, classes_names)
