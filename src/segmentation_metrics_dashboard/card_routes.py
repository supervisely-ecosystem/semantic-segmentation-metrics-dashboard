from fastapi import Depends, HTTPException

import src.segmentation_metrics_dashboard.card_widgets as card_widgets
import src.sly_globals as g
import supervisely
from supervisely.app import DataJson, StateJson
from supervisely.app.fastapi import run_sync
from supervisely.app.widgets import ElementButton










