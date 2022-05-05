import asyncio
import json
import time

from fastapi import Depends, HTTPException
from scipy.sparse import data
from starlette.responses import JSONResponse

import supervisely
from supervisely import logger

import src.select_input_projects.card_widgets as card_widgets
import src.select_input_projects.card_functions as card_functions

from supervisely.app import DataJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton

import src.sly_globals as g
import src.sly_functions as f


@card_widgets.download_projects_button.add_route(app=g.app, route=ElementButton.Routes.BUTTON_CLICKED)
def download_selected_projects(state: supervisely.app.StateJson = Depends(supervisely.app.StateJson.from_request)):
    card_widgets.download_projects_button.loading = True
    card_widgets.pred_project_selector.disabled = True
    card_widgets.gt_project_selector.disabled = True
    run_sync(DataJson().synchronize_changes())

    try:
        card_functions.download_project(project_selector_widget=card_widgets.gt_project_selector,
                                        state=state, project_dir=g.gt_project_dir)

        card_functions.download_project(project_selector_widget=card_widgets.pred_project_selector,
                                        state=state, project_dir=g.pred_project_dir)

        with card_widgets.download_projects_progress(message='converting GT project',
                                                     total=f.get_project_items_count(g.gt_project_dir)) as pbar:

            f.convert_project_to_semantic_segmentation_task(src_project_dir=g.gt_project_dir,
                                                            dst_project_dir=g.gt_project_dir_converted,
                                                            progress_cb=pbar.update)

        with card_widgets.download_projects_progress(message='converting PRED project',
                                                     total=f.get_project_items_count(g.pred_project_dir)) as pbar:
            f.convert_project_to_semantic_segmentation_task(src_project_dir=g.pred_project_dir,
                                                            dst_project_dir=g.pred_project_dir_converted,
                                                            progress_cb=pbar.update)

        DataJson()['datasets_table_content'] = card_functions.get_datasets_table_content(
            gt_project_dir=g.gt_project_dir,
            pred_project_dir=g.pred_project_dir)

        g.gt_project['workspace_id'] = card_widgets.gt_project_selector.get_selected_workspace_id(state)
        g.gt_project['project_id'] = card_widgets.gt_project_selector.get_selected_project_id(state)

        g.pred_project['workspace_id'] = card_widgets.pred_project_selector.get_selected_workspace_id(state)
        g.pred_project['project_id'] = card_widgets.pred_project_selector.get_selected_project_id(state)

        card_widgets.download_projects_button.disabled = True
        DataJson()['current_step'] += 1
    except Exception as ex:
        card_widgets.pred_project_selector.disabled = False
        card_widgets.gt_project_selector.disabled = False

        logger.warn(f'Cannot download projects: {repr(ex)}', exc_info=True)
        raise HTTPException(status_code=500, detail={'title': "Cannot download projects",
                                                     'message': f'Please select input data and try again'})

    finally:
        card_widgets.download_projects_button.loading = False
        run_sync(DataJson().synchronize_changes())
