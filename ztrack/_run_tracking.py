def run_tracking(
    inputs,
    recursive,
    overwrite,
    verbose,
    ignore_errors,
):
    import warnings

    import pandas as pd

    from ztrack.tracking import get_trackers_from_config
    from ztrack.utils.exception import VideoTrackingError
    from ztrack.utils.file import (
        get_config_dict,
        get_results_path,
        get_video_paths_from_inputs,
    )

    videos = get_video_paths_from_inputs(inputs, recursive, overwrite)
    for video in videos:
        config = get_config_dict(video)
        trackers = get_trackers_from_config(config, verbose=verbose)

        dfs = {}

        for key, tracker in trackers.items():

            if verbose:
                print(f"Tracking {video}")

            try:
                dfs[key] = tracker.track_video(video, ignore_errors)
            except VideoTrackingError as e:
                warnings.warn(
                    f"Tracker {key} failed for {video} at frame {e.frame}."
                )

        if dfs:
            s = pd.HDFStore(get_results_path(video))

            for key, df in dfs.items():
                s[key] = df

            s.close()
