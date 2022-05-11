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
        card_functions.refill_images_table(table_content=g.images_table_content)
        card_widgets.images_gallery.clean_up()
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

    selected_cell = card_widgets.matched_pixels_matrix.get_selected_cell(state)
    cell_data = selected_cell['cell_data']

    gt_selected_class = cell_data['row_name']
    pred_selected_class = cell_data['col_name']

    filtered_items = card_functions.get_filtered_items_by_classes_names(gt_selected_class, pred_selected_class)

    images_table_filtered = card_functions.get_filtered_table(filtered_items=filtered_items)
    card_functions.refill_images_table(table_content=images_table_filtered)

    card_widgets.matched_pixels_matrix.loading = False
    toggle_iri_button(state=state)


@card_widgets.stats_by_classes_table.add_route(g.app, route=card_widgets.stats_by_classes_table.Routes.CELL_CLICKED)
def classes_table_cell_clicked(state: StateJson = Depends(StateJson.from_request)):
    selected_cell = card_widgets.stats_by_classes_table.get_selected_cell(state)
    if selected_cell['row_data'] is None or selected_cell['row_data'].get('class_name') is None:
        return

    class_name = selected_cell['row_data']['class_name']

    filtered_items = card_functions.get_filtered_items_by_classes_names(class_name, class_name)

    images_table_filtered = card_functions.get_filtered_table(filtered_items=filtered_items)
    card_functions.refill_images_table(table_content=images_table_filtered)

    toggle_iri_button(state=state)


@card_widgets.stats_by_datasets_table.add_route(g.app, route=card_widgets.stats_by_datasets_table.Routes.CELL_CLICKED)
def datasets_table_cell_clicked(state: StateJson = Depends(StateJson.from_request)):
    selected_cell = card_widgets.stats_by_datasets_table.get_selected_cell(state)
    if selected_cell['row_data'] is None or selected_cell['row_data'].get('ds_name') is None:
        return

    ds_name = selected_cell['row_data']['ds_name']

    filtered_items = card_functions.get_filtered_items_by_ds_names(ds_names=[ds_name])

    images_table_filtered = card_functions.get_filtered_table(filtered_items=filtered_items)
    card_functions.refill_images_table(table_content=images_table_filtered)

    toggle_iri_button(state=state)


@card_widgets.images_table.add_route(g.app, route=card_widgets.images_table.Routes.CELL_CLICKED)
def table_cell_clicked(state: StateJson = Depends(StateJson.from_request)):
    selected_cell = card_widgets.images_table.get_selected_cell(state)
    if selected_cell['row_data'] is None or selected_cell['row_data'].get('ds name') is None:
        return

    DataJson()['image_to_analyze_selected'] = True
    card_functions.refill_image_gallery(state)
    card_widgets.image_matrix.data = card_functions.get_matrix_for_image_content(state)

    run_sync(DataJson().synchronize_changes())


@card_widgets.image_matrix.add_route(g.app, route=card_widgets.image_matrix.Routes.CELL_CLICKED)
def image_matrix_cell_clicked(state: StateJson = Depends(StateJson.from_request)):

    card_functions.highlight_selected_class_on_images(state)
    run_sync(DataJson().synchronize_changes())
















