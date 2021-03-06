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
    selected_datasets_names = state['selectedDatasets']

    selected_datasets_names = list(set(selected_datasets_names).intersection(set(DataJson()['allowed_datasets_names'])))

    if len(selected_datasets_names) == 0:
        raise HTTPException(status_code=500, detail={'title': "Matched datasets not selected",
                                                     'message': f'Please select datasets and try again'})

    card_widgets.select_datasets_button.loading = True
    run_sync(DataJson().synchronize_changes())

    g.ds2matched = {}
    g.ds2matched_backup = None

    DataJson()['classes_table_content'] = card_functions.get_classes_table_content(selected_datasets_names)
    card_functions.cache_datasets_infos(selected_datasets_names)

    card_widgets.ds_done_label.text = f'<b>{", ".join(selected_datasets_names) if len(selected_datasets_names) < 5 else len(selected_datasets_names)}</b> datasets selected'

    card_widgets.select_datasets_button.loading = False

    DataJson()['current_step'] += 1
    DataJson()['selected_datasets_names'] = selected_datasets_names

    run_sync(DataJson().synchronize_changes())
    run_sync(state.synchronize_changes())


@card_widgets.reselect_datasets_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def reselect_datasets_button_clicked(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    DataJson()['current_step'] = 2
    run_sync(DataJson().synchronize_changes())
