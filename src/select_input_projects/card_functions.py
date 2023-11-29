import os
from datetime import time

import supervisely as sly
from supervisely.app import StateJson, DataJson
from supervisely.app.widgets import ProjectSelector

import src.select_input_projects.card_widgets as card_widgets

import src.sly_functions as f
import src.sly_globals as g


def _split_images_by_cache(images, cache):
    images_to_download = []
    images_in_cache = []
    images_cache_paths = []
    for image in images:
        _, effective_ext = os.path.splitext(image.name)
        if len(effective_ext) == 0:
            # Fallback for the old format where we were cutting off extensions from image names.
            effective_ext = image.ext
        cache_path = cache.check_storage_object(image.hash, effective_ext)
        if cache_path is None:
            images_to_download.append(image)
        else:
            images_in_cache.append(image)
            images_cache_paths.append(cache_path)
    return images_to_download, images_in_cache, images_cache_paths


def _maybe_append_image_extension(name, ext):
    name_split = os.path.splitext(name)
    if name_split[1] == "":
        normalized_ext = ("." + ext).replace("..", ".")
        result = name + normalized_ext
        sly.image.validate_ext(result)
    else:
        result = name
    return result

def _download_dataset(
    api: sly.Api,
    dataset,
    dataset_id,
    cache=None,
    progress_cb=None,
    project_meta: sly.ProjectMeta = None,
    only_image_tags=False,
    save_image_info=False,
    save_images=True,
):
    images = api.image.get_list(dataset_id)
    images_to_download = images
    if only_image_tags is True:
        if project_meta is None:
            raise ValueError("Project Meta is not defined")
        id_to_tagmeta = project_meta.tag_metas.get_id_mapping()

    # copy images from cache to task folder and download corresponding annotations
    if cache:
        (
            images_to_download,
            images_in_cache,
            images_cache_paths,
        ) = _split_images_by_cache(images, cache)
        if len(images_to_download) + len(images_in_cache) != len(images):
            raise RuntimeError("Error with images cache during download. Please contact support.")
        sly.logger.info(
            f"Download dataset: {dataset.name}",
            extra={
                "total": len(images),
                "in cache": len(images_in_cache),
                "to download": len(images_to_download),
            },
        )
        if len(images_in_cache) > 0:
            img_cache_ids = [img_info.id for img_info in images_in_cache]

            if only_image_tags is False:
                ann_info_list = api.annotation.download_batch(
                    dataset_id, img_cache_ids, progress_cb
                )
                img_name_to_ann = {ann.image_id: ann.annotation for ann in ann_info_list}
            else:
                img_name_to_ann = {}
                for image_info in images_in_cache:
                    tags = sly.TagCollection.from_api_response(
                        image_info.tags, project_meta.tag_metas, id_to_tagmeta
                    )
                    tmp_ann = sly.Annotation(
                        img_size=(image_info.height, image_info.width), img_tags=tags
                    )
                    img_name_to_ann[image_info.id] = tmp_ann.to_json()
                if progress_cb is not None:
                    progress_cb(len(images_in_cache))

            for batch in sly.batched(list(zip(images_in_cache, images_cache_paths)), batch_size=50):
                for img_info, img_cache_path in batch:
                    item_name = _maybe_append_image_extension(img_info.name, img_info.ext)
                    img_info_to_add = None
                    if save_image_info is True:
                        img_info_to_add = img_info
                    dataset.add_item_file(
                        item_name,
                        item_path=img_cache_path if save_images is True else None,
                        ann=img_name_to_ann[img_info.id],
                        _validate_item=False,
                        _use_hardlink=True,
                        item_info=img_info_to_add,
                    )
                if progress_cb is not None:
                    progress_cb(len(batch))

    # download images from server
    if len(images_to_download) > 0:
        # prepare lists for api methods
        img_ids = []
        img_paths = []
        for img_info in images_to_download:
            img_ids.append(img_info.id)
            img_paths.append(
                os.path.join(
                    dataset.item_dir,
                    _maybe_append_image_extension(img_info.name, img_info.ext),
                )
            )

        # download annotations
        if only_image_tags is False:
            ann_info_list = api.annotation.download_batch(dataset_id, img_ids, progress_cb)
            img_name_to_ann = {ann.image_id: ann.annotation for ann in ann_info_list}
        else:
            img_name_to_ann = {}
            for image_info in images_to_download:
                tags = sly.TagCollection.from_api_response(
                    image_info.tags, project_meta.tag_metas, id_to_tagmeta
                )
                tmp_ann = sly.Annotation(img_size=(image_info.height, image_info.width), img_tags=tags)
                img_name_to_ann[image_info.id] = tmp_ann.to_json()
            if progress_cb is not None:
                progress_cb(len(images_to_download))

        # download images and write to dataset
        for idx, img_info_batch in enumerate(sly.batched(images_to_download)):
            if save_images:
                images_ids_batch = [image_info.id for image_info in img_info_batch]
                images_nps = api.image.download_nps(
                    dataset_id, images_ids_batch, progress_cb=progress_cb
                )
                if len(images_to_download) > 200 and idx % 2 == 0:
                    sly.logger.debug(f"Downloaded {idx * 50 + len(images_nps)} images. Pause 0.1 sec.") 
                    time.sleep(0.1)
            else:
                images_nps = [None] * len(img_info_batch)
            for index, image_np in enumerate(images_nps):
                img_info = img_info_batch[index]
                image_name = _maybe_append_image_extension(img_info.name, img_info.ext)

                dataset.add_item_np(
                    item_name=image_name,
                    img=image_np if save_images is True else None,
                    ann=img_name_to_ann[img_info.id],
                    img_info=img_info if save_image_info is True else None,
                )
        if cache is not None and save_images is True:
            img_hashes = [img_info.hash for img_info in images_to_download]
            cache.write_objects(img_paths, img_hashes)



def download_project(project_selector_widget: ProjectSelector, state: StateJson, project_dir):
    project_info = g.api.project.get_info_by_id(project_selector_widget.get_selected_project_id(state))
    pbar = card_widgets.download_projects_progress(message=f'downloading projects', total=project_info.items_count * 2)

    if os.path.exists(project_dir):
        sly.fs.clean_dir(project_dir)

    try:
        raise Exception("Oops")
        sly.download_project(g.api, project_info.id, project_dir, cache=g.file_cache,
                                 progress_cb=pbar.update, save_image_info=True)
    except Exception as e:
        pbar = card_widgets.download_projects_progress(message=f'downloading projects', total=project_info.items_count * 2)
        sly.logger.debug(f"Failed download project, error: {e}")
        sly.logger.debug("Trying to download project dataset by dataset")
        if os.path.exists(project_dir):
            sly.fs.clean_dir(project_dir)
        project_fs = sly.Project(project_dir, sly.OpenMode.CREATE)
        meta = sly.ProjectMeta.from_json(g.api.project.get_meta(project_info.id))
        project_fs.set_meta(meta)
        for dataset_info in g.api.dataset.get_list(project_info.id):
            dataset_name = dataset_info.name
            dataset = project_fs.create_dataset(dataset_name)
            _download_dataset(
                g.api,
                dataset,
                dataset_info.id,
                cache=g.file_cache,
                progress_cb=pbar.update,
                project_meta=meta,
                only_image_tags=False,
                save_image_info=True,
                save_images=True,
            )
            sly.logger.debug(f"{dataset_info.name} downloaded. Pause 1 sec.")
            time.sleep(1)
        


######################################
# @TODO: move to DatasetsCompare widget
######################################

def get_dataset_formatted_info(dataset_info: sly.Dataset = None):
    if dataset_info is not None:
        items_num = len(dataset_info.get_items_names())
        return {'name': dataset_info.name,
                'count': items_num}
    else:
        return {'name': '',
                'count': 0}


def get_datasets_statuses(gt_dataset_info: sly.Dataset, pred_dataset_info: sly.Dataset):
    matched_and_unmatched_images_names = f.get_matched_and_unmatched_images_names(gt_dataset_info, pred_dataset_info)

    return {
        'matched': len(matched_and_unmatched_images_names['matched_images_names']),
        'gt_unique': len(matched_and_unmatched_images_names['gt_unique_images_names']),
        'pred_unique': len(matched_and_unmatched_images_names['pred_unique_images_names'])
    }


def get_datasets_table_content(gt_project_dir, pred_project_dir):
    def format_dataset_statuses(statuses_dict):
        formatted_statuses = {
            'numbers': [
                statuses_dict.get('matched', 0),
                statuses_dict.get('all_unmatched', 0),
                statuses_dict.get('gt_unique', 0),
                statuses_dict.get('pred_unique', 0),
                statuses_dict.get('gt_unmatched', 0),
                statuses_dict.get('pred_unmatched', 0),
            ],
            'colors': [
                '#008000FF',
                '#FF0000FF',
                '#20A0FFFF',
                '#20A0FFFF',
                '#FF0000FF',
                '#FF0000FF',
            ],
            'icons': [
                ["zmdi zmdi-check"],
                ["zmdi zmdi-close"],
                ["zmdi zmdi-long-arrow-left", "zmdi zmdi-plus-circle-o"],
                ["zmdi zmdi-plus-circle-o", "zmdi zmdi-long-arrow-right"],
                ["zmdi zmdi-close"],
                ["zmdi zmdi-close"],
            ],
            'messages': [
                'MATCHED',
                'UNMATCHED',
                'UNIQUE (GT)',
                'UNIQUE (PRED)',
                'UNMATCHED (GT)',
                'UNMATCHED (PRED)',
            ]
        }
        return formatted_statuses

    DataJson()['allowed_datasets_names'] = []

    # reading datasets
    gt_datasets = f.get_datasets_dict_by_project_dir(directory=gt_project_dir)
    pred_datasets = f.get_datasets_dict_by_project_dir(directory=pred_project_dir)

    table_content = []

    # fill table by datasets
    for gt_ds_name, gt_dataset_info in gt_datasets.items():
        row_in_table: dict = {}
        unformatted_statuses: dict = {}

        pred_dataset_info: sly.Dataset = pred_datasets.get(gt_ds_name)

        if pred_dataset_info is not None:  # if dataset exists on both sides
            row_in_table['left'] = get_dataset_formatted_info(gt_dataset_info)
            row_in_table['right'] = get_dataset_formatted_info(pred_dataset_info)

            unformatted_statuses.update(get_datasets_statuses(gt_dataset_info, pred_dataset_info))
            if unformatted_statuses['matched'] == 0:
                unformatted_statuses.update({'all_unmatched': -1,
                                             'gt_unique': 0,
                                             'pred_unique': 0})
            else:
                DataJson()['allowed_datasets_names'].append(gt_ds_name)

        else:
            row_in_table['left'] = get_dataset_formatted_info(gt_dataset_info)
            row_in_table['right'] = get_dataset_formatted_info()
            unformatted_statuses.update({'pred_unmatched': -1})

        row_in_table['statuses'] = format_dataset_statuses(unformatted_statuses)

        table_content.append(row_in_table)

    # don't forget about right unique side
    for pred_ds_name, pred_dataset_info in pred_datasets.items():

        if gt_datasets.get(pred_ds_name) is None:
            row_in_table = {
                'left': get_dataset_formatted_info(),
                'right': get_dataset_formatted_info(pred_dataset_info),
                'statuses': format_dataset_statuses({'gt_unmatched': -1})
            }
            table_content.append(row_in_table)

    return table_content

######################################
# @TODO: move to ProjectsCompare widget
######################################
