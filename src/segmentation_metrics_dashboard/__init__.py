from supervisely.app import StateJson

from src.segmentation_metrics_dashboard.card_routes import *
from src.segmentation_metrics_dashboard.card_functions import *
from src.segmentation_metrics_dashboard.card_widgets import *

StateJson()['showIRI'] = False
DataJson()['image_to_analyze_selected'] = False

DataJson()['general_metrics'] = {
    'accuracy': {
        'value': 0,
        'color': 'black',
    },
    'iou': {
        'value': 0,
        'color': 'black',
    },

    'border_color': 'black'
}



