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
import time


@card_widgets.select_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def select_input_classes(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    total_start_time = time.time()
    selected_classes_names = set(state['selectedClasses'])
    selected_classes_names = list(set(selected_classes_names).intersection(set(DataJson()['allowed_classes_names'])))

    if len(selected_classes_names) == 0:
        raise HTTPException(status_code=500, detail={'title': "Matched or Converted classes not selected",
                                                     'message': f'Please select classes and try again'})

    card_widgets.select_classes_button.loading = True
    run_sync(DataJson().synchronize_changes())

    DataJson()['selected_classes_names'] = selected_classes_names

    apply_start_time = time.time()
    card_functions.apply_classes_to_projects(selected_classes_names)
    apply_end_time = time.time()
    print(f"Total apply_classes_to_projects function execution time: {apply_end_time - apply_start_time} seconds")
    card_functions.filter_matched_items_by_classes(selected_classes_names)

    scores_start_time = time.time()
    card_functions.calculate_scores_tables(gt_project_dir=g.gt_project_dir_converted,
                                           pred_project_dir=g.pred_project_dir_converted)
    scores_end_time = time.time()
    print(f"Total calculate_scores_tables function execution time: {scores_end_time - scores_start_time} seconds")

    DataJson()['general_metrics']['accuracy']['value'] = round(seg_functions.calculate_general_pixel_accuracy(), 3)
    DataJson()['general_metrics']['iou']['value'] = round(seg_functions.calculate_general_mean_iou(), 3)
    seg_functions.colorize_metrics()

    # fill matrix and tables
    seg_widgets.matched_pixels_matrix.read_pandas(seg_functions.get_matches_pixels_matrix_content()) # matches matrix

    stats_tables_content = seg_functions.get_stats_tables_content()
    seg_widgets.stats_by_classes_table.read_pandas(stats_tables_content['classes'])  # stats by classes
    seg_widgets.stats_by_datasets_table.read_pandas(stats_tables_content['datasets'])  # stats by classes

    g.images_table_content = seg_functions.get_images_table_content()

    seg_widgets.images_table.read_pandas(pd.DataFrame(data=[list(row.values()) for row in g.images_table_content],
                                                      columns=list(g.images_table_content[0].keys())))

    # card_widgets.classes_done_label.text = f'<b>{", ".join(selected_classes_names) if len(selected_classes_names) < 5 else len(selected_classes_names)}</b> classes selected'
    card_widgets.classes_done_label.text = f'metrics successfully calculated'
    card_widgets.select_classes_button.loading = False

    seg_widgets.toggle_iri_button.disabled = False
    seg_widgets.toggle_iri_button.text = 'Open Images Review Interface without filters <i style="margin-left: 5px" class="zmdi zmdi-collection-image"></i>'
    state['showIRI'] = False

    DataJson()['image_to_analyze_selected'] = False

    DataJson()['current_step'] += 1

    run_sync(state.synchronize_changes())
    run_sync(DataJson().synchronize_changes())
    total_end_time = time.time()
    print(f"Total select_input_classes function execution time: {total_end_time - total_start_time} seconds")
    percent_scores = round(((scores_end_time - scores_start_time) / (total_end_time - total_start_time)) * 100, 2)
    print(f"Execution of function calculate_scores_tables takes {percent_scores} % of time for execution of function select_input_classes")
    percent_apply = round(((apply_end_time - apply_start_time) / (total_end_time - total_start_time)) * 100, 2)
    print(f"Execution of function apply_classes_to_projects takes {percent_apply} % of time for execution of function select_input_classes")


@card_widgets.reselect_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_classes_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    DataJson()['current_step'] = 3
    run_sync(DataJson().synchronize_changes())
