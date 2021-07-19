from ztrack._settings import config_extension, video_extensions
from ztrack.gui.create_config import CreateConfigWindow
from ztrack.gui.utils.launch import launch
from ztrack.utils.file import extract_video_paths


def create_config(
    inputs,
    recursive,
    same_config,
    overwrite,
    verbose,
):
    video_paths, save_paths = extract_video_paths(
        inputs,
        recursive,
        same_config,
        overwrite,
        config_extension,
        video_extensions,
    )
    launch(
        CreateConfigWindow,
        videoPaths=video_paths,
        savePaths=save_paths,
        verbose=verbose,
    )
