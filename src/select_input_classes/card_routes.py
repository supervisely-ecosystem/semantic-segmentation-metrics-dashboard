from fastapi import Depends, HTTPException

import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g

import src.select_input_classes.card_widgets as card_widgets
import src.select_input_classes.card_functions as card_functions


@card_widgets.select_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def select_input_classes(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    selected_classes = state['selectedClasses']
    if len(selected_classes) == 0:
        raise HTTPException(status_code=500, detail={'title': "Classes not selected",
                                                     'message': f'Please select classes and try again'})

    card_widgets.select_classes_button.loading = True

    card_functions.convert_projects_to_semantic_segmentation_task(selected_classes)

    # fill tables and matrix

    # state['showIRI'] = True

    card_widgets.select_classes_button.loading = False
    card_widgets.select_classes_button.disabled = True
    DataJson()['current_step'] += 1

    run_sync(StateJson().synchronize_changes())
    run_sync(DataJson().synchronize_changes())







