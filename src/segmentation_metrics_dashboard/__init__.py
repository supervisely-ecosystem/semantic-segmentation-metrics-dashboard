from supervisely.app import StateJson

from src.segmentation_metrics_dashboard.card_routes import *
from src.segmentation_metrics_dashboard.card_functions import *
from src.segmentation_metrics_dashboard.card_widgets import *

StateJson()['showIRI'] = False

DataJson()['pixel_accuracy'] = 0.6
DataJson()['iou'] = 0.8


