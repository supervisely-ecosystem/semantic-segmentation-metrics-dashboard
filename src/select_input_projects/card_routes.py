import asyncio
import time

from fastapi import Depends

import supervisely
from supervisely import logger

import src.select_input_projects.card_widgets as card_widgets
import src.select_input_projects.card_functions as card_functions


from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g


@card_widgets.download_projects_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_projects(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.download_projects_button.loading = True
    card_widgets.pred_project_selector.disabled = True
    card_widgets.gt_project_selector.disabled = True
    run_sync(DataJson().synchronize_changes())

    card_functions.download_project(project_selector_widget=card_widgets.gt_project_selector,
                                    state=state, project_dir=g.gt_project_dir)

    card_functions.download_project(project_selector_widget=card_widgets.gt_project_selector,
                                    state=state, project_dir=g.gt_project_dir)

    card_widgets.download_projects_button.disabled = True
    card_widgets.download_projects_button.loading = False
    run_sync(DataJson().synchronize_changes())





