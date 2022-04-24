from fastapi import Depends

import supervisely
from supervisely import logger

import src.select_input_projects.card_widgets as card_widgets
from supervisely.app.widgets import ElementButton

import src.sly_globals as g


@card_widgets.download_projects_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_projects(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):

    print(state)
    print(card_widgets.pred_project_selector.get_selected_project_id(state))




