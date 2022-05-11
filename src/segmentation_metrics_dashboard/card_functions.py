import colorsys
import copy

from supervisely.app import DataJson
import numpy as np
import pandas as pd

import supervisely
import src.sly_globals as g
import src.sly_functions as f

import src.segmentation_metrics_dashboard.card_widgets as card_widgets
from supervisely.app.fastapi import run_sync


def get_pixel_accuracy_for_image(image_stats):
    current_image_score = []

    for current_class_name, current_class_matches in image_stats.items():
        class_score = current_class_matches.get(current_class_name)

        if class_score is not None:
            current_image_score.append(class_score)

    return round(sum(current_image_score) / len(current_image_score), 3)  # from 0 to 1


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

            # sum_of_row = sum(list(row.values()))
            # row = [round((row[class_name] / sum_of_row), 3) for class_name in classes_names]
            row = [round((row[class_name]), 5) for class_name in classes_names]
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

    return pd.DataFrame(data=existing_class_matrix.round(4), columns=existing_class_names)


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
            stats_by_datasets[ds_name]['accuracy'] = round(
                sum(classname2matched.values()) / len(classname2matched.values()), 3)
            stats_by_datasets[ds_name]['matched'] = len(matched_images_in_dataset)

    # collecting iou
    for ds_name, scores_by_images_in_dataset in g.iou_scores.items():

        # per classes
        scores_by_classes_in_dataset = {class_name: [] for class_name in classes_names}

        for current_image in scores_by_images_in_dataset.values():
            for class_name_on_image, class_score in current_image.items():
                scores_by_classes_in_dataset[class_name_on_image].append(class_score)

        classname2score = {class_name: round(sum(scores_list) / len(scores_list), 3) for class_name, scores_list in
                           scores_by_classes_in_dataset.items() if len(scores_list) > 0}

        for class_name, class_score in classname2score.items():
            stats_by_class_names[class_name]['mean iou'].append(class_score)

        # per datasets
        if len(classname2score.values()) > 0:
            stats_by_datasets[ds_name]['mean iou'] = round(
                sum(classname2score.values()) / len(classname2score.values()), 3)

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
                    round(sum(stats_by_class_names[class_name][score_key]) / len(
                        stats_by_class_names[class_name][score_key]), 3)
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
                accuracy = round(get_pixel_accuracy_for_image(image_stats=pixels_matches), 3)
            else:
                accuracy = '-'

            iou_scores = g.iou_scores.get(ds_name, {}).get(item_name)
            scores_per_class = {class_name: None for class_name in selected_classes_names}

            if iou_scores is not None:
                mean_iou = round(sum(list(iou_scores.values())) / len(iou_scores), 3)
                scores_per_class.update(iou_scores)
            else:
                mean_iou = '-'

            for class_name in selected_classes_names:
                scores_per_class[f'{class_name} IoU'] = scores_per_class.pop(class_name)

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
                'item name': item_name,
                'gt image': f'<a href="{gt_image_url}" rel="noopener noreferrer" target="_blank">open <i class="zmdi zmdi-open-in-new" style="margin-left: 5px"></i></a>',
                'pred image': f'<a href="{pred_image_url}" rel="noopener noreferrer" target="_blank">open <i class="zmdi zmdi-open-in-new" style="margin-left: 5px"`></i></a>',
                'accuracy': accuracy,
                'mean IoU': mean_iou,
                **scores_per_class
            })

    # table_content.update(iou_by_classes)
    return table_content


def get_matrix_for_image_content(state):
    selected_classes_names = DataJson()['selected_classes_names']
    selected_cell = card_widgets.images_table.get_selected_cell(state)

    ds_name = selected_cell['row_data']['ds name']
    item_name = selected_cell['row_data']['item name']

    item_info = g.pixels_matches[ds_name][item_name]

    matrix_for_image = get_matched_pixels_matrix_for_image(current_image=item_info,
                                                           classes_names=selected_classes_names)

    columns_indexes_to_remove = []
    for class_name_index, class_name_data in enumerate(matrix_for_image):
        if len(class_name_data) == 0:
            columns_indexes_to_remove.append(class_name_index)
            matrix_for_image[class_name_index] = [0 for _ in range(len(selected_classes_names))]

    # adding predicted, but not presented in GT classes
    matrix_for_image = np.asarray(matrix_for_image)
    columns_sum = np.sum(matrix_for_image, axis=0)

    filtered_columns_to_remove = []
    for index_to_remove in columns_indexes_to_remove:
        if not (columns_sum[index_to_remove] > 0):
            filtered_columns_to_remove.append(index_to_remove)

    matrix_for_image = np.delete(matrix_for_image, filtered_columns_to_remove, axis=0)
    matrix_for_image = np.delete(matrix_for_image, filtered_columns_to_remove, axis=1)
    selected_classes_names = np.delete(selected_classes_names, filtered_columns_to_remove, axis=0)

    return pd.DataFrame(data=matrix_for_image, columns=selected_classes_names)


def get_matches_annotation(gt_ann: supervisely.Annotation, pred_ann: supervisely.Annotation, selected_classes=None):
    gt_mask, gt_name2color = f.get_mask_with_colors_mapping(gt_ann)
    pred_mask, pred_name2color = f.get_mask_with_colors_mapping(pred_ann)

    gt_mask, pred_mask = np.asarray(gt_mask), np.asarray(pred_mask)

    if selected_classes is None:
        matched_pixels, unmatched_pixels = np.zeros(gt_ann.img_size), np.zeros(gt_ann.img_size)
        selected_classes = DataJson()['selected_classes_names']
        for selected_class in selected_classes:
            gt_color = gt_name2color.get(selected_class)
            pred_color = pred_name2color.get(selected_class)

            if gt_color is not None and pred_color is None:
                gt_unmatched = (gt_mask == gt_color).all(-1)
                unmatched_pixels = np.logical_or(gt_unmatched, unmatched_pixels)
            elif gt_color is None and pred_color is not None:
                pred_unmatched = (pred_mask == pred_color).all(-1)
                unmatched_pixels = np.logical_or(pred_unmatched, unmatched_pixels)

            elif gt_color is not None and pred_color is not None:
                gt_pixels_of_interest = (gt_mask == gt_color).all(-1)
                pred_pixels_of_interest = (pred_mask == pred_color).all(-1)

                matched_pixels_for_class = np.logical_and(gt_pixels_of_interest, pred_pixels_of_interest)
                unmatched_pixels_for_class = np.logical_xor(gt_pixels_of_interest, pred_pixels_of_interest)

                matched_pixels = np.logical_or(matched_pixels_for_class, matched_pixels)
                unmatched_pixels = np.logical_or(unmatched_pixels_for_class, unmatched_pixels)
    else:
        gt_class, pred_class = selected_classes[0], selected_classes[1]
        gt_color, pred_color = gt_name2color[gt_class], pred_name2color[pred_class]

        gt_interest, pred_interest = np.asarray(gt_mask == gt_color).all(-1), np.asarray(pred_mask == pred_color).all(
            -1)

        if gt_class == pred_class:
            matched_pixels = np.logical_and(gt_interest, pred_interest)
            unmatched_pixels = np.logical_xor(gt_interest, matched_pixels)
        else:
            matched_pixels = np.zeros(gt_ann.img_size)
            unmatched_pixels = np.logical_and(gt_interest, pred_interest)

    labels_list = []
    if np.sum(matched_pixels) > 0:
        matched_bitmap = supervisely.Bitmap(data=matched_pixels)
        label_matched = supervisely.Label(matched_bitmap, supervisely.ObjClass('_matched_pixels', supervisely.Bitmap,
                                                                               color=[0, 255, 0]))
        labels_list.append(label_matched)

    if np.sum(unmatched_pixels) > 0:
        unmatched_bitmap = supervisely.Bitmap(data=unmatched_pixels)
        label_unmatched = supervisely.Label(unmatched_bitmap,
                                            supervisely.ObjClass('_unmatched_pixels', supervisely.Bitmap,
                                                                 color=[255, 0, 0]))
        labels_list.append(label_unmatched)

    return supervisely.Annotation(img_size=gt_ann.img_size, labels=labels_list)


def refill_image_gallery(state, selected_classes=None):
    selected_cell = card_widgets.images_table.get_selected_cell(state)

    if selected_cell['row_data'] is None or selected_cell['row_data'].get('ds name') is None:
        return

    card_widgets.images_gallery.loading = True
    card_widgets.image_matrix.loading = True
    run_sync(DataJson().synchronize_changes())

    ds_name = selected_cell['row_data']['ds name']
    item_name = selected_cell['row_data']['item name']

    gt_image_url = f.get_image_link(project_dir=g.gt_project_dir, ds_name=ds_name, item_name=item_name)
    gt_annotation = f.get_image_annotation(project_dir=g.gt_project_dir_converted, ds_name=ds_name, item_name=item_name)

    pred_image_url = f.get_image_link(project_dir=g.pred_project_dir, ds_name=ds_name, item_name=item_name)
    pred_annotation = f.get_image_annotation(project_dir=g.pred_project_dir_converted, ds_name=ds_name,
                                             item_name=item_name)

    result_image_url = gt_image_url
    result_annotation = get_matches_annotation(gt_ann=gt_annotation, pred_ann=pred_annotation,
                                               selected_classes=selected_classes)

    if selected_classes is not None:
        gt_annotation = f.filter_annotation_by_selected_classes(gt_annotation, [selected_classes[0]])
        pred_annotation = f.filter_annotation_by_selected_classes(pred_annotation, [selected_classes[1]])

    card_widgets.images_gallery.clean_up()

    gt_title = 'GT'
    pred_title = 'PRED'
    if selected_classes is not None:
        gt_title += f': {selected_classes[0]}'
        pred_title += f': {selected_classes[1]}'

    card_widgets.images_gallery.append(title=gt_title, image_url=gt_image_url, annotation=gt_annotation, column_index=0)
    card_widgets.images_gallery.append(title='RESULTS: GREEN MATCHED / RED UNMATCHED', image_url=result_image_url,
                                       annotation=result_annotation, column_index=1)
    card_widgets.images_gallery.append(title=pred_title, image_url=pred_image_url, annotation=pred_annotation,
                                       column_index=2)

    card_widgets.images_gallery.loading = False
    card_widgets.image_matrix.loading = False


def highlight_selected_class_on_images(state):
    selected_cell = card_widgets.image_matrix.get_selected_cell(state)
    cell_data = selected_cell['cell_data']

    gt_selected_class = cell_data['row_name']
    pred_selected_class = cell_data['col_name']

    refill_image_gallery(state, selected_classes=[gt_selected_class, pred_selected_class])


def get_filtered_items_by_classes_names(gt_selected_class, pred_selected_class):
    filtered_items = {ds_name: [] for ds_name in g.ds2matched.keys()}

    for ds_name, items_names in g.ds2matched.items():
        ds_db = g.pixels_matches.get(ds_name, {})

        for item_name in items_names:
            gt_classes_to_matches = ds_db.get(item_name, None)
            if gt_classes_to_matches is None:
                continue

            matches_for_gt = gt_classes_to_matches.get(gt_selected_class, {})
            matching_score = matches_for_gt.get(pred_selected_class, 0)
            if matching_score > 0:
                filtered_items[ds_name].append(item_name)

    return filtered_items


def get_filtered_table(filtered_items):
    filtered_table = []
    for row in g.images_table_content:
        if filtered_items.get(row['ds name']) is not None and row['item name'] in filtered_items[row['ds name']]:
            filtered_table.append(row)

    return filtered_table


def refill_images_table(table_content):
    if len(table_content) > 0:
        card_widgets.images_table.data = pd.DataFrame(data=[list(row.values()) for row in table_content],
                                                      columns=list(table_content[0].keys()))
    else:
        card_widgets.images_table.data = pd.DataFrame(data=[], columns=[])


def get_filtered_items_by_ds_names(ds_names):
    filtered_items = {ds_name: [] for ds_name in g.ds2matched.keys()}

    for ds_name, items_names in g.ds2matched.items():
        if ds_name not in ds_names:
            continue

        filtered_items[ds_name] = items_names
    return filtered_items
