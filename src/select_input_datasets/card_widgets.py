

from supervisely.app.widgets import ElementButton, DoneLabel

import src.sly_globals as g

select_datasets_button = ElementButton(text='select datasets', button_type='primary')
reselect_datasets_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect', button_type='warning', button_size='small', plain=True)

ds_done_label = DoneLabel()


