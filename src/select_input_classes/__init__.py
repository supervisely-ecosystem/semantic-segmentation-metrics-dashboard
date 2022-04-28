from supervisely.app import StateJson

from src.select_input_classes.card_routes import *
from src.select_input_classes.card_functions import *
from src.select_input_classes.card_widgets import *

DataJson()['classes_table_content'] = None
StateJson()['selectedClasses'] = []

DataJson()['allowed_classes_names'] = []
DataJson()['selected_classes_names'] = []


