import pandas as pd
from fastapi import Depends, HTTPException

import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g
import src.sly_functions as f

import src.segmentation_metrics_dashboard.card_functions as seg_functions
import src.segmentation_metrics_dashboard.card_widgets as seg_widgets


import src.select_input_classes.card_widgets as card_widgets
import src.select_input_classes.card_functions as card_functions


@card_widgets.select_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def select_input_classes(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    selected_classes_names = set(state['selectedClasses'])
    selected_classes_names = list(set(selected_classes_names).intersection(set(DataJson()['allowed_classes_names'])))
    if len(selected_classes_names) == 0:
        raise HTTPException(status_code=500, detail={'title': "Matched or Converted classes not selected",
                                                     'message': f'Please select classes and try again'})

    card_widgets.select_classes_button.loading = True
    run_sync(DataJson().synchronize_changes())

    DataJson()['selected_classes_names'] = selected_classes_names

    card_functions.apply_classes_to_projects(selected_classes_names)

    card_functions.calculate_scores_tables(gt_project_dir=g.gt_project_dir_converted,
                                           pred_project_dir=g.pred_project_dir_converted)

    DataJson()['general_metrics']['accuracy']['value'] = round(seg_functions.calculate_general_pixel_accuracy(), 3)
    DataJson()['general_metrics']['iou']['value'] = round(seg_functions.calculate_general_mean_iou(), 3)
    seg_functions.colorize_metrics()

    # fill matrix and tables
    seg_widgets.matched_pixels_matrix.data = seg_functions.get_matches_pixels_matrix_content()  # matches matrix

    stats_tables_content = seg_functions.get_stats_tables_content()
    seg_widgets.stats_by_classes_table.data = stats_tables_content['classes']  # stats by classes
    seg_widgets.stats_by_datasets_table.data = stats_tables_content['datasets']  # stats by classes

    g.images_table_content = seg_functions.get_images_table_content()

    seg_widgets.images_table.data = pd.DataFrame(data=[list(row.values()) for row in g.images_table_content],
                                                 columns=list(g.images_table_content[0].keys()))

    # seg_widgets.matched_pixels_matrix.data = seg_functions.get_matches_pixels_matrix_content()  # stats by ds


    # state['showIRI'] = True

    card_widgets.select_classes_button.loading = False
    card_widgets.select_classes_button.disabled = True
    DataJson()['current_step'] += 1

    run_sync(StateJson().synchronize_changes())
    run_sync(DataJson().synchronize_changes())
