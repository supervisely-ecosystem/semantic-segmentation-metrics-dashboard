from fastapi import Depends, HTTPException

import src.select_input_classes.card_widgets as card_widgets
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson
from supervisely.app.widgets import ElementButton


@card_widgets.select_classes_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_projects(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    selected_datsets = state['selectedClasses']
    if len(selected_datsets) == 0:
        raise HTTPException(status_code=500, detail={'title': "Classes not selected",
                                                     'message': f'Please select classes and try again'})






