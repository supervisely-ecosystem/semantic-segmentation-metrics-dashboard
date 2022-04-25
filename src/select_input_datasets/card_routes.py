import asyncio
import json
import time

from fastapi import Depends, HTTPException
from scipy.sparse import data
from starlette.responses import JSONResponse

import supervisely
from supervisely import logger

import src.select_input_datasets.card_widgets as card_widgets
import src.select_input_datasets.card_functions as card_functions

from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g


@card_widgets.select_datasets_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_projects(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    pass
    # card_widgets.download_projects_button.loading = True
    # card_widgets.pred_project_selector.disabled = True
    # card_widgets.gt_project_selector.disabled = True
    # run_sync(DataJson().synchronize_changes())
    #
    # try:
    #     card_functions.download_project(project_selector_widget=card_widgets.gt_project_selector,
    #                                     state=state, project_dir=g.gt_project_dir)
    #
    #     card_functions.download_project(project_selector_widget=card_widgets.gt_project_selector,
    #                                     state=state, project_dir=g.gt_project_dir)
    #
    #     card_widgets.download_projects_button.disabled = True
    #     DataJson()['current_step'] += 1
    # except Exception as ex:
    #     card_widgets.pred_project_selector.disabled = False
    #     card_widgets.gt_project_selector.disabled = False
    #
    #     logger.warn(f'Cannot download projects: {repr(ex)}')
    #     raise HTTPException(status_code=500, detail={'title': "Cannot download projects", 'message': f'Please select input data and try again'})
    #
    # finally:
    #     card_widgets.download_projects_button.loading = False
    #     run_sync(DataJson().synchronize_changes())
