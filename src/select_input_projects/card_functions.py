from datetime import time

import src.select_input_projects.card_widgets as card_widgets

import src.sly_globals as g
import supervisely
from supervisely.app import StateJson
from supervisely.app.widgets import ProjectSelector


def download_project(project_selector_widget: ProjectSelector, state: StateJson, project_dir):
    project_info = g.api.project.get_info_by_id(project_selector_widget.get_selected_project_id(state))
    pbar = card_widgets.download_projects_progress(message='downloading projects', total=project_info.items_count * 2)

    supervisely.fs.clean_dir(project_dir)
    supervisely.download_project(g.api, project_info.id, project_dir, cache=g.file_cache,
                                 progress_cb=pbar.update, save_image_info=True)
