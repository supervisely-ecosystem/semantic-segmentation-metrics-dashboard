import pbar as pbar
from fastapi import Depends, HTTPException

import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g
import src.sly_functions as f

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

    with card_widgets.select_classes_progress(message='applying classes to GT',
                                              total=f.get_project_items_count(g.gt_project_dir)) as pbar:
        f.convert_project_to_semantic_segmentation_task(target_classes_names_list=selected_classes_names,
                                                        src_project_dir=g.gt_project_dir,
                                                        dst_project_dir=g.gt_project_dir_converted,
                                                        progress_cb=pbar.update)

    with card_widgets.select_classes_progress(message='applying classes to PRED',
                                              total=f.get_project_items_count(g.gt_project_dir)) as pbar:
        f.convert_project_to_semantic_segmentation_task(target_classes_names_list=selected_classes_names,
                                                        src_project_dir=g.pred_project_dir,
                                                        dst_project_dir=g.pred_project_dir_converted,
                                                        progress_cb=pbar.update)

    card_functions.calculate_base_metrics(gt_project_dir=g.gt_project_dir_converted,
                                          pred_project_dir=g.pred_project_dir_converted)

    # fill tables and matrix

    # state['showIRI'] = True

    card_widgets.select_classes_button.loading = False
    card_widgets.select_classes_button.disabled = True
    DataJson()['current_step'] += 1

    run_sync(StateJson().synchronize_changes())
    run_sync(DataJson().synchronize_changes())
