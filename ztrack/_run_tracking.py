from pathlib import Path
from typing import List, Tuple

from ztrack._settings import video_extensions
from ztrack.tracking import get_trackers_from_config
from ztrack.utils.file import (get_config_dict, get_config_path,
                               get_results_path)


def get_video_paths_from_inputs(
    inputs: List[str],
    recursive: bool,
    overwrite: bool,
    video_suffixes: Tuple[str, ...],
):
    paths: List[Path] = list(map(Path, inputs))
    videos = [
        path
        for path in paths
        if path.is_file() and path.suffix in video_suffixes
    ]

    for path in filter(Path.is_dir, paths):
        for ext in video_suffixes:
            videos.extend(
                path.rglob(f"*{ext}") if recursive else path.glob(f"*{ext}")
            )

    videos = [file for file in videos if get_config_path(file).exists()]

    if not overwrite:
        videos = [
            file for file in videos if not get_results_path(file).exists()
        ]

    return videos


def run_tracking(
    inputs,
    recursive,
    overwrite,
    verbose,
):
    videos = get_video_paths_from_inputs(
        inputs, recursive, overwrite, video_extensions
    )
    print(videos)
    for video in videos:
        config = get_config_dict(video)
        print(get_trackers_from_config(config))
