import supervisely


def get_datasets_dict_by_project_dir(directory):
    project = supervisely.Project(directory=directory, mode=supervisely.OpenMode.READ)
    return {key: value for key, value in zip(project.datasets.keys(), project.datasets.items())}
