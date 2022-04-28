from src.select_input_datasets.card_routes import *
from src.select_input_datasets.card_functions import *
from src.select_input_datasets.card_widgets import *
from supervisely.app import StateJson

DataJson()['datasets_table_content'] = None
StateJson()['selectedDatasets'] = []


DataJson()['allowed_datasets_names'] = []
DataJson()['selected_datasets_names'] = []



