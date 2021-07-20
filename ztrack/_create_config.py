from ztrack._settings import config_extension, video_extensions
from ztrack.gui.create_config import CreateConfigWindow
from ztrack.gui.utils.launch import launch
from ztrack.utils.file import get_paths_for_config_creation


def create_config(
    inputs,
    recursive,
    same_config,
    overwrite,
    verbose,
):
    video_paths, save_paths = get_paths_for_config_creation(inputs, recursive, same_config, overwrite)
    launch(
        CreateConfigWindow,
        videoPaths=video_paths,
        savePaths=save_paths,
        verbose=verbose,
    )
