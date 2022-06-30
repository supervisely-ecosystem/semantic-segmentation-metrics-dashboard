from fastapi import Request, Depends
from supervisely.app import StateJson
from supervisely.app.fastapi import available_after_shutdown

import src.sly_globals as g

import src.select_input_projects
import src.select_input_datasets
import src.select_input_classes
import src.segmentation_metrics_dashboard



# @TODO: hide confusion matrix totals (row / col)
# @TODO: confusion visualize all TP/FN (?) by specific class
# @TODO: ? fixed colors to blue mask


@g.app.get("/")
@available_after_shutdown(app=g.app)
def read_index(request: Request = None):
    return g.templates_env.TemplateResponse('index.html', {'request': request})


@g.app.on_event("shutdown")
def shutdown():
    read_index()  # save last version of static files


@g.app.post("/apply_changes/")
async def apply_changes(state: StateJson = Depends(StateJson.from_request)):
    await state.synchronize_changes()
