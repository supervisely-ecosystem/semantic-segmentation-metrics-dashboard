

from supervisely.app.widgets import ElementButton, SlyTqdm, DoneLabel

select_classes_button = ElementButton(text='select classes', button_type='primary')
reselect_classes_button = ElementButton(text='<i style="margin-right: 5px" class="zmdi zmdi-rotate-left"></i>reselect', button_type='warning', button_size='small', plain=True)

select_classes_progress = SlyTqdm()

classes_done_label = DoneLabel()


