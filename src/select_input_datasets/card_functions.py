import numpy

import src.sly_functions as f
import src.sly_globals as g
import supervisely


######################################
# @TODO: move to ClassesCompare widget
######################################
from supervisely.app import DataJson


def update_objects_info(objects_info, image_annotation):
    objects_on_image = set([label.obj_class for label in image_annotation.labels])
    # labels_area = sum([label.area for label in image_annotation.labels])

    for object_on_image in objects_on_image:
        objects_info.setdefault(object_on_image.name, {
            'count': 0,
            'area': 0,
            'name': object_on_image.name,
            'color': '#%02x%02x%02x' % tuple(object_on_image.color),
            'shape': object_on_image.geometry_type.geometry_name(),
        })

        objects_info[object_on_image.name]['count'] += 1
        # objects_info[object_on_image.name]['area'] += labels_area

    objects_info['images_area'] = objects_info.get('images_area', 0) + numpy.prod(image_annotation.img_size)


def update_matched_info(matched_objects_info, gt_image_annotation, pred_image_annotation):
    gt_obj_names = set([label.obj_class.name for label in gt_image_annotation.labels])
    pred_obj_names = set([label.obj_class.name for label in pred_image_annotation.labels])

    object_names_intersected = gt_obj_names.intersection(pred_obj_names)

    for intersected_name in object_names_intersected:
        matched_objects_info[intersected_name] = matched_objects_info.get(intersected_name, 0) + 1


def update_objects_areas(objects_info, image_annotation):
    name2area = {label.obj_class.name: label.area for label in image_annotation.labels}

    for name, area in name2area.items():
        if objects_info.get(name) is not None:
            objects_info[name]['area'] += area


def collect_objects_information(objects_info, selected_datasets_names, gt_project_dir, pred_project_dir,
                                collect_matched_images_names=True, mode='info'):

    gt_project_meta = supervisely.Project(directory=gt_project_dir, mode=supervisely.OpenMode.READ).meta
    pred_project_meta = supervisely.Project(directory=pred_project_dir, mode=supervisely.OpenMode.READ).meta

    # reading datasets
    gt_datasets = f.get_datasets_dict_by_project_dir(directory=gt_project_dir)
    pred_datasets = f.get_datasets_dict_by_project_dir(directory=pred_project_dir)

    for selected_ds_name in selected_datasets_names:
        gt_dataset_info = gt_datasets.get(selected_ds_name)
        pred_dataset_info = pred_datasets.get(selected_ds_name)

        if pred_dataset_info is None or gt_dataset_info is None:
            continue

        if collect_matched_images_names is True:
            images_names = f.get_matched_and_unmatched_images_names(gt_dataset_info=gt_dataset_info,
                                                                    pred_dataset_info=pred_dataset_info)
            g.ds2matched[selected_ds_name] = images_names['matched_images_names']
        else:
            images_names = {'matched_images_names': g.ds2matched[selected_ds_name]}

        for matched_image_name in images_names['matched_images_names']:
            gt_image_ann: supervisely.Annotation = gt_dataset_info.get_ann(matched_image_name, gt_project_meta)
            pred_image_ann: supervisely.Annotation = pred_dataset_info.get_ann(matched_image_name, pred_project_meta)

            if mode == 'info':
                # getting stats for each class
                update_objects_info(objects_info['gt'], gt_image_ann)
                update_objects_info(objects_info['pred'], pred_image_ann)

                # getting stats for matched classes
                update_matched_info(objects_info['matched'], gt_image_ann, pred_image_ann)

            elif mode == 'area':
                update_objects_areas(objects_info['gt'], gt_image_ann)
                update_objects_areas(objects_info['pred'], pred_image_ann)

            else:
                raise ValueError('mode must be info or area')


def convert_areas_to_percentage(objects_info):
    images_area = objects_info.pop('images_area')
    for object_info in objects_info.values():
        object_info['area'] = round((object_info['area'] / images_area * 100), 2)


def get_class_formatted_info(class_info=None):
    if class_info is not None:
        return class_info
    else:
        return {
            'name': '',
            'shape': '',
            'color': '#ffffff',
            'count': 0,
            'area': 0
        }


def get_classes_statuses(gt_class_stats, pred_class_stats):
    supported_shapes = [
        supervisely.Bitmap.geometry_name(),
        supervisely.Polygon.geometry_name(),
        # supervisely.Rectangle.geometry_name(),
    ]

    shapes_unmatched = not (gt_class_stats['shape'] in supported_shapes and pred_class_stats['shape'] in supported_shapes)
    shapes_converted = gt_class_stats['shape'] != supervisely.Bitmap.geometry_name() or \
                       pred_class_stats['shape'] != supervisely.Bitmap.geometry_name()

    return {
        'matched': 0,
        'converted': -1 if shapes_converted and not shapes_unmatched else 0,
        'unmatched': -1 if shapes_unmatched else 0
    }


def get_formatted_table_content(objects_info):
    def format_statuses(statuses_dict):
        formatted_statuses = {
            'numbers': [
                statuses_dict.get('matched', 0),
                statuses_dict.get('converted', 0),
                statuses_dict.get('shape_unmatched', 0),
                statuses_dict.get('pair_unmatched', 0),
            ],
            'colors': [
                '#008000FF',
                '#0487d7',
                '#FF0000FF',
                '#FF0000FF',
            ],
            'icons': [
                ["zmdi zmdi-check"],
                ["zmdi zmdi-ungroup"],
                ["zmdi zmdi-close"],
                ["zmdi zmdi-close"],
            ],
            'messages': [
                'MATCHED',
                'CONVERTED',
                'SHAPES UNMATCHED',
                'PAIR NOT FOUND'
            ]
        }
        return formatted_statuses

    DataJson()['allowed_classes_names'] = []
    table_content = []

    for gt_class_name, gt_class_stats in objects_info['gt'].items():

        row_in_table: dict = {}
        unformatted_statuses: dict = {}

        pred_class_stats = objects_info['pred'].get(gt_class_name)
        if pred_class_stats is not None:  # if class exists on both sides
            row_in_table['left'] = get_class_formatted_info(gt_class_stats)
            row_in_table['right'] = get_class_formatted_info(pred_class_stats)

            unformatted_statuses.update(get_classes_statuses(gt_class_stats, pred_class_stats))
            if unformatted_statuses['unmatched'] != -1 and unformatted_statuses['converted'] != -1:
                unformatted_statuses['matched'] = objects_info['matched'][gt_class_name]
            elif unformatted_statuses['converted'] == -1:
                unformatted_statuses['converted'] = objects_info['matched'][gt_class_name]
            elif unformatted_statuses['unmatched'] == -1:
                unformatted_statuses['shape_unmatched'] = -1

            if unformatted_statuses['unmatched'] != -1:
                DataJson()['allowed_classes_names'].append(gt_class_name)

        else:
            row_in_table['left'] = get_class_formatted_info(gt_class_stats)
            row_in_table['right'] = get_class_formatted_info()
            unformatted_statuses.update({'pair_unmatched': -1})

        row_in_table['statuses'] = format_statuses(unformatted_statuses)

        table_content.append(row_in_table)

    # don't forget about right unique side
    for pred_class_name, pred_class_stats in objects_info['pred'].items():
        if objects_info['gt'].get(pred_class_name) is None:
            row_in_table = {
                'left': get_class_formatted_info(),
                'right': get_class_formatted_info(pred_class_stats),
                'statuses': format_statuses({'pair_unmatched': -1})
            }
            table_content.append(row_in_table)

    return table_content


def get_classes_table_content(selected_datasets_names):
    objects_info = {
        'gt': {},
        'pred': {},
        'matched': {}
    }

    # collecting objects information
    collect_objects_information(objects_info, selected_datasets_names, g.gt_project_dir, g.pred_project_dir)
    collect_objects_information(objects_info, selected_datasets_names,
                                g.gt_project_dir_converted, g.pred_project_dir_converted,
                                collect_matched_images_names=False, mode='area')

    convert_areas_to_percentage(objects_info['gt'])
    convert_areas_to_percentage(objects_info['pred'])

    return get_formatted_table_content(objects_info)

######################################
# @TODO: move to ClassesCompare widget
######################################


def cache_datasets_infos(selected_datasets_names):
    g.gt_ds2info = {}
    g.pred_ds2info = {}
    for selected_dataset_name in selected_datasets_names:
        g.gt_ds2info[selected_dataset_name] = g.api.dataset.get_info_by_name(parent_id=g.gt_project['project_id'], name=selected_dataset_name)
        g.pred_ds2info[selected_dataset_name] = g.api.dataset.get_info_by_name(parent_id=g.pred_project['project_id'], name=selected_dataset_name)
