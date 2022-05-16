from fastapi import Request, Depends
from supervisely.app import StateJson

import src.sly_globals as g

import src.select_input_projects
import src.select_input_datasets
import src.select_input_classes
import src.segmentation_metrics_dashboard


# @TODO: hide confusion matrix totals (row / col)
# @TODO: confusion visualize all TP/FN (?) by specific class
# @TODO: ? fixed colors to blue mask


@g.app.get("/")
def read_index(request: Request):
    return g.templates_env.TemplateResponse('index.html', {'request': request})


@g.app.post("/apply_changes/")
async def apply_changes(state: StateJson = Depends(StateJson.from_request)):
    await state.synchronize_changes()
