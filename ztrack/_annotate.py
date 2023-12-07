def annotate(
    inputs,
    recursive,
    verbose,
):
    from ztrack.gui.annotator import Annotator
    from ztrack.gui.utils.launch import launch
    from ztrack.utils.file import get_paths_for_view_results

    video_paths = [str(i) for i in get_paths_for_view_results(inputs, recursive)]

    launch(
        Annotator,
        videoPaths=video_paths,
        verbose=verbose,
    )
