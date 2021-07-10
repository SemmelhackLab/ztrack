from ztrack.gui.create_config import CreateConfigWindow
from ztrack.utils.file import extract_video_paths


def create_config(
    inputs,
    recursive,
    same_config,
    overwrite,
    verbose,
):
    video_paths, save_paths = extract_video_paths(
        inputs, recursive, same_config, overwrite
    )
