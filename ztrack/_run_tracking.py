import pandas as pd

from ztrack.tracking import get_trackers_from_config
from ztrack.utils.file import (get_config_dict, get_results_path,
                               get_video_paths_from_inputs)
from ztrack.utils.exception import TrackingError


def run_tracking(
    inputs,
    recursive,
    overwrite,
    verbose,
):
    videos = get_video_paths_from_inputs(inputs, recursive, overwrite)
    for video in videos:
        config = get_config_dict(video)
        trackers = get_trackers_from_config(config, verbose=verbose)
        s = pd.HDFStore(get_results_path(video))
        for key, tracker in trackers.items():
            print(f"Tracking {video}")
            try:
                s[key] = tracker.track_video(video)
            except TrackingError:
                print(f"Tracking error for {video}")
        s.close()
