from ztrack.gui.tracking_viewer import TrackingViewer
from ztrack.gui.utils.launch import launch
from ztrack.utils.file import get_paths_for_view_results


def view_results(
    inputs,
    recursive,
    verbose,
):
    video_paths = [str(i) for i in get_paths_for_view_results(inputs, recursive)]
    launch(
        TrackingViewer,
        videoPaths=video_paths,
        verbose=verbose,
    )
