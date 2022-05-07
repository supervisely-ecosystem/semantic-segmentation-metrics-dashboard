import pandas as pd

from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery, NotificationBox

toggle_iri_button = ElementButton(text='Open Images Review Interface <i style="margin-left: 5px" class="zmdi zmdi-collection-image"></i>', button_type='warning', button_size='small')
toggle_iri_button.disabled = True


matched_pixels_matrix = ConfusionMatrix()

stats_by_classes_table = ClassicTable()
stats_by_datasets_table = ClassicTable()

images_table = ClassicTable(fixed_columns_num=6)
images_gallery = GridGallery(columns_number=3, enable_zoom=False, sync_views=True)
image_matrix = ConfusionMatrix()

notification_box_inside_iri = NotificationBox(title="Image isn't selected", description='select image from table to view results')


