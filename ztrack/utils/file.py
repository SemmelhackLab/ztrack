import json
from pathlib import Path
from typing import List, Optional, Tuple

from ztrack._settings import config_extension, results_extension


def get_results_path(video):
    return Path(str(video) + results_extension)


def get_config_path(video):
    return Path(str(video) + config_extension)


def get_config_dict(video) -> Optional[dict]:
    path = get_config_path(video)

    if path.exists():
        with open(path) as fp:
            try:
                return json.load(fp)
            except json.JSONDecodeError:
                return None
    return None


def get_paths_for_config_creation(
    inputs: List[str],
    recursive: bool,
    same_config: bool,
    overwrite: bool,
    results_suffix: str,
    video_suffixes: Tuple[str, ...],
):
    def _str(path: Path):
        return path.resolve().as_posix()

    paths: List[Path] = [Path(path) for path in inputs]
    directories = [path for path in paths if path.is_dir()]
    files = [
        path
        for path in paths
        if path.is_file() and path.suffix in video_suffixes
    ]

    video_paths: List[str] = []
    save_paths: List[List[str]] = []

    for directory in directories:
        for ext in video_suffixes:
            if recursive:
                videos = list(directory.rglob(f"*{ext}"))
            else:
                videos = list(directory.glob(f"*{ext}"))

            if not overwrite:
                videos = [
                    video
                    for video in videos
                    if not video.with_suffix(results_suffix).exists()
                ]

            if len(videos) > 0:
                if same_config:
                    video_paths.append(_str(videos[0]))
                    save_paths.append([_str(video) for video in videos])
                else:
                    for video in videos:
                        video_paths.append(_str(video))
                        save_paths.append([_str(video)])

    if not overwrite:
        files = [
            file
            for file in files
            if not file.with_suffix(results_suffix).exists()
        ]

    for file in files:
        video_paths.append(_str(file))
        save_paths.append([_str(file)])

    return video_paths, save_paths
