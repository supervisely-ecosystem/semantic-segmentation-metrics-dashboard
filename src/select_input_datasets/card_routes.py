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
    selected_datsets = state['selectedDatasets']
    if len(selected_datsets) == 0:
        raise HTTPException(status_code=500, detail={'title': "Datasets not selected",
                                                     'message': f'Please select datasets and try again'})

    card_widgets.select_datasets_button.loading = True
    run_sync(DataJson().synchronize_changes())

    card_functions.get_classes_table_content(selected_datsets)

    card_widgets.select_datasets_button.loading = False
    card_widgets.select_datasets_button.disabled = True
    DataJson()['current_step'] += 1

    run_sync(DataJson().synchronize_changes())





