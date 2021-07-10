from pathlib import Path
from typing import List, Tuple


def _str(path: Path):
    return path.resolve().as_posix()


def extract_video_paths(
    inputs: List[str],
    recursive: bool,
    same_config: bool,
    overwrite: bool,
    suffix: str,
    video_extensions: Tuple[str, ...],
):
    paths: List[Path] = [Path(path) for path in inputs]
    directories = [path for path in paths if path.is_dir()]
    files = [path for path in paths if path.is_file()]

    video_paths: List[str] = []
    save_paths: List[List[str]] = []

    for directory in directories:
        for ext in video_extensions:
            if recursive:
                videos = list(directory.rglob(f"*{ext}"))
            else:
                videos = list(directory.glob(f"*{ext}"))

            if not overwrite:
                videos = [
                    video
                    for video in videos
                    if not video.with_suffix(suffix).exists()
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
            file for file in files if not file.with_suffix(suffix).exists()
        ]

    for file in files:
        video_paths.append(_str(file))
        save_paths.append([_str(file)])

    return video_paths, save_paths
