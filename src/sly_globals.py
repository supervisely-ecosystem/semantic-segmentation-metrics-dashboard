import os
from pathlib import Path

from fastapi import FastAPI

from supervisely import FileCache
from supervisely.app import StateJson, DataJson
from supervisely.sly_logger import logger
from starlette.staticfiles import StaticFiles

import supervisely
from supervisely.app.fastapi import create, Jinja2Templates, enable_hot_reload_on_debug

import dotenv

dotenv.load_dotenv('/Users/qanelph/Desktop/work/supervisely/segmentation-metrics-dashboard/debug.env')
dotenv.load_dotenv('/Users/qanelph/Desktop/work/supervisely/private/secret_debug.env')


TEAM_ID = int(os.environ.get('TEAM_ID'))

app_root_directory = str(Path(__file__).parent.absolute().parents[0])
app_cache_dir = os.path.join(app_root_directory, 'tempfiles', 'cache')

logger.info(f"App root directory: {app_root_directory}")

api: supervisely.Api = supervisely.Api.from_env()
file_cache = FileCache(name="FileCache", storage_root=app_cache_dir)
app = FastAPI()
sly_app = create()


app.mount("/sly", sly_app)
app.mount("/static", StaticFiles(directory=os.path.join(app_root_directory, 'static')), name="static")

templates_env = Jinja2Templates(directory=os.path.join(app_root_directory, 'templates'))

DataJson()['current_step'] = 1


gt_project = {
    'workspace_id': 0,
    'project_id': 0
}
pred_project = {
    'workspace_id': 0,
    'project_id': 0
}

gt_project_dir = os.path.join(app_root_directory, 'tempfiles', 'gt_project_dir')
pred_project_dir = os.path.join(app_root_directory, 'tempfiles', 'pred_project_dir')

gt_project_dir_converted = os.path.join(app_root_directory, 'tempfiles', 'gt_project_dir_converted')
pred_project_dir_converted = os.path.join(app_root_directory, 'tempfiles', 'pred_project_dir_converted')

ds2matched = {}
ds2matched_backup = None

gt_ds2info = {}
pred_ds2info = {}

datasets_names_to_analyze = []

bg_class_name = '__bg__'


pixels_matches = {}

"""
structure: ds -> image -> 
{
    'class_1': {
        'class_1': intersection: float, 
        'class_2': intersection: float, 
        ...
        },
        'class_2': {...}
    },
    ...   
}
"""

images_accuracy = {}
"""
structure: ds -> image -> accuracy 
"""


iou_scores = {}

"""
structure: ds -> image -> 
{
    'class_1': iou: float,
    'class_2': iou: float,
    ...   
}
"""

images_table_content = None

"""
table structure:
{
    'ds name': [],
    'gt image': [],
    'pred image': [],
    'pixels accuracy': [],
    'mean iou': [],
    'matched classes': [],
    **iou_by_classes
}
"""



