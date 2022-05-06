import pandas as pd
from fastapi import Depends, HTTPException

import src.segmentation_metrics_dashboard.card_widgets as card_widgets
import src.segmentation_metrics_dashboard.card_functions as card_functions
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync


def toggle_iri_button(state):
    state['showIRI'] = not state['showIRI']

    if state['showIRI'] is not True:
        card_widgets.toggle_iri_button.text = 'Open Images Review Interface <i style="margin-left: 5px" class="zmdi zmdi-collection-image"></i>'
    else:
        card_widgets.toggle_iri_button.text = 'Back To Statistics <i style="margin-left: 5px" class="zmdi zmdi-chart"></i>'

    run_sync(DataJson().synchronize_changes())
    run_sync(state.synchronize_changes())


@card_widgets.toggle_iri_button.add_route(g.app, route=card_widgets.toggle_iri_button.Routes.BUTTON_CLICKED)
def toggle_iri_button_wrapper(state: StateJson = Depends(StateJson.from_request)):
    toggle_iri_button(state)


@card_widgets.matched_pixels_matrix.add_route(g.app, route=card_widgets.matched_pixels_matrix.Routes.CELL_CLICKED)
def matched_pixels_matrix_cell_clicked(state: StateJson = Depends(StateJson.from_request)):
    DataJson()['image_to_analyze_selected'] = False
    card_widgets.matched_pixels_matrix.loading = True
    run_sync(DataJson().synchronize_changes())

    filtered_items = card_functions.get_filtered_items_by_classes_names(state)

    images_table_filtered = card_functions.get_filtered_table(filtered_items=filtered_items)
    card_widgets.images_table.data = pd.DataFrame(data=[list(row.values()) for row in images_table_filtered],
                                                  columns=list(images_table_filtered[0].keys()))

    toggle_iri_button(state=state)


@card_widgets.images_table.add_route(g.app, route=card_widgets.images_table.Routes.CELL_CLICKED)
def table_cell_clicked(state: StateJson = Depends(StateJson.from_request)):
    DataJson()['image_to_analyze_selected'] = True

    card_functions.refill_image_gallery(state)
    card_widgets.image_matrix.data = card_functions.get_matrix_for_image_content(state)

    run_sync(DataJson().synchronize_changes())


@card_widgets.image_matrix.add_route(g.app, route=card_widgets.image_matrix.Routes.CELL_CLICKED)
def image_matrix_cell_clicked(state: StateJson = Depends(StateJson.from_request)):

    card_functions.highlight_selected_class_on_images(state)
    run_sync(DataJson().synchronize_changes())
















