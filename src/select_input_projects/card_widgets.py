

from supervisely.app.widgets import ProjectSelector, ElementButton


import src.sly_globals as g

gt_project_selector = ProjectSelector(team_id=g.TEAM_ID, team_is_selectable=False, datasets_is_selectable=False)
pred_project_selector = ProjectSelector(team_id=g.TEAM_ID, team_is_selectable=False, datasets_is_selectable=False)

download_projects_button = ElementButton(text='download projects', button_type='primary')
