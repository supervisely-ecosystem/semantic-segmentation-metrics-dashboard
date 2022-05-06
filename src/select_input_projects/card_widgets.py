

from supervisely.app.widgets import ProjectSelector, ElementButton, SlyTqdm, DoneLabel

import src.sly_globals as g

gt_project_selector = ProjectSelector(team_id=g.TEAM_ID, team_is_selectable=False, datasets_is_selectable=False)
pred_project_selector = ProjectSelector(team_id=g.TEAM_ID, team_is_selectable=False, datasets_is_selectable=False)

download_projects_button = ElementButton(text='SELECT', button_type='primary')

download_projects_progress = SlyTqdm(message='')

projects_downloaded_done_label = DoneLabel()

