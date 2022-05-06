from fastapi import Depends, HTTPException

import src.segmentation_metrics_dashboard.card_widgets as card_widgets
import src.segmentation_metrics_dashboard.card_functions as card_functions
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync


@card_widgets.images_table.add_route(g.app, route=card_widgets.images_table.Routes.CELL_CLICKED)
def table_cell_clicked(state: StateJson = Depends(StateJson.from_request)):

    card_functions.refill_image_gallery(state)
    card_widgets.image_matrix.data = card_functions.get_matrix_for_image_content(state)

    run_sync(DataJson().synchronize_changes())


@card_widgets.image_matrix.add_route(g.app, route=card_widgets.image_matrix.Routes.CELL_CLICKED)
def image_matrix_cell_clicked(state: StateJson = Depends(StateJson.from_request)):

    card_functions.highlight_selected_class_on_images(state)
    run_sync(DataJson().synchronize_changes())


@card_widgets.open_iri_button.add_route(g.app, route=card_widgets.open_iri_button.Routes.BUTTON_CLICKED)
def open_iri_button(state: StateJson = Depends(StateJson.from_request)):
    state['showIRI'] = True
    run_sync(state.synchronize_changes())














