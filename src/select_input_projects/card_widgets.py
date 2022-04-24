

from supervisely.app.widgets import ProjectSelector, ElementButton

import src.select_input_projects.card_handlers as card_functions
import src.sly_globals as g

gt_project_selector = ProjectSelector(team_id=g.TEAM_ID, team_is_selectable=False, datasets_is_selectable=False)
pred_project_selector = ProjectSelector(team_id=g.TEAM_ID, team_is_selectable=False, datasets_is_selectable=False)

button_routes = ElementButton.Routes(app=g.app, button_clicked=card_functions.download_selected_projects)
download_projects_button = ElementButton(widget_routes=button_routes, button_type='primary')
