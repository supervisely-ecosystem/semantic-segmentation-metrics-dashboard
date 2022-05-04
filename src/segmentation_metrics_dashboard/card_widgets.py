from supervisely.app.widgets import ElementButton, ConfusionMatrix, ClassicTable, GridGallery

open_iri_button = ElementButton(text='Open Images Review Interface', button_type='primary')
matched_pixels_matrix = ConfusionMatrix()

stats_by_classes_table = ClassicTable()
stats_by_datasets_table = ClassicTable()

images_table = ClassicTable()
images_gallery = GridGallery(columns_number=3)
image_matrix = ConfusionMatrix()






