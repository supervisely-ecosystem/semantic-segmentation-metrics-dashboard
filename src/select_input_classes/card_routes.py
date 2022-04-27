from fastapi import Depends, HTTPException

import src.select_input_classes.card_widgets as card_widgets
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton


@card_widgets.select_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def select_input_classes(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    selected_classes = state['selectedClasses']
    if len(selected_classes) == 0:
        raise HTTPException(status_code=500, detail={'title': "Classes not selected",
                                                     'message': f'Please select classes and try again'})

    card_widgets.select_classes_button.loading = True

    # fill tables and matrix

    card_widgets.select_classes_button.loading = False
    card_widgets.select_classes_button.disabled = True
    DataJson()['current_step'] += 1

    run_sync(DataJson().synchronize_changes())







