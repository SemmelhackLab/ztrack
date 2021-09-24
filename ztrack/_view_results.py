from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from decord import VideoReader
from tqdm import tqdm

import ztrack.utils.cv as zcv
from ztrack.gui.tracking_viewer import TrackingViewer
from ztrack.gui.utils.launch import launch
from ztrack.utils.file import get_paths_for_view_results


def view_results(
    inputs,
    recursive,
    gui,
    codec,
    fps,
    line_width,
    frame_range,
    format,
    timer,
    egocentric,
    width,
    front,
    behind,
    verbose,
):
    video_paths = [
        str(i) for i in get_paths_for_view_results(inputs, recursive)
    ]

    if gui:
        launch(
            TrackingViewer,
            videoPaths=video_paths,
            verbose=verbose,
        )
    else:
        for video_path in video_paths:
            generate_tracking_video(
                video_path,
                codec=codec,
                fps=fps,
                line_width=line_width,
                frame_range=frame_range,
                verbose=verbose,
                format=format,
                timer=timer,
                egocentric=egocentric,
                width=width,
                front=front,
                behind=behind,
            )


def generate_tracking_video(
    video_path,
    *,
    results_path=None,
    save_path=None,
    codec: str,
    format: str,
    fps=None,
    line_width=2,
    frame_range=None,
    timer,
    egocentric,
    width,
    front,
    behind,
    verbose=0,
):
    colors = dict(
        left_eye=(0, 0, 255),
        right_eye=(255, 0, 0),
        swim_bladder=(0, 255, 0),
        tail=(255, 0, 255),
    )
    line_type = cv2.LINE_AA

    if results_path is None:
        results_path = str(video_path) + ".h5"
        assert Path(results_path).exists()

    if save_path is None:
        save_path = str(video_path) + "." + format

    store = pd.HDFStore(results_path)

    df_eye = None
    df_tail = None

    if "free" in store:
        try:
            df = store["free"]
            df_eye = df[["left_eye", "right_eye", "swim_bladder", "heading"]]
            tail_columns = [j for j in df.columns if "point" in j[0]]
            df_tail = df.loc[:, tail_columns]
        except KeyError:
            pass

    if df_eye is None and "eye" in store:
        df_eye = store["eye"]
    if df_tail is None and "tail" in store:
        df_tail = store["tail"]

    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*codec)

    if fps is None:
        fps = int(cap.get(cv2.CAP_PROP_FPS))

    if df_eye is None:
        egocentric = False

    midpoints = None

    if egocentric:
        w = width
        h = front + behind

        midpoints = (
            np.column_stack(
                [
                    df_eye[("left_eye", "cx")] + df_eye[("right_eye", "cx")],
                    df_eye[("left_eye", "cy")] + df_eye[("right_eye", "cy")],
                ]
            )
            / 2
        )

    else:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(save_path, fourcc, fps, (w, h), True)

    if frame_range is None:
        frame_range = range(0, int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
    elif isinstance(frame_range, tuple):
        frame_range = range(*frame_range)

    cap.release()

    if verbose:
        frame_range = tqdm(frame_range)

    vr = VideoReader(video_path)

    for i in frame_range:
        img = vr[i].asnumpy()

        if df_eye is not None:
            row_eye = df_eye.iloc[i]

            if egocentric:
                heading = row_eye["heading"].item()
                img = zcv.warp_img(
                    img, midpoints[i], heading, width, front, behind
                )
            else:
                for blob in ("left_eye", "right_eye", "swim_bladder"):
                    cx, cy, a, b, angle, *_ = row_eye[blob]
                    center = (round(cx), round(cy))
                    axes = (round(a), round(b))
                    cv2.ellipse(
                        img,
                        center,
                        axes,
                        angle,
                        0,
                        360,
                        colors[blob],
                        line_width,
                        line_type,
                    )

        if df_tail is not None and not egocentric:
            row_tail = df_tail.iloc[i]

            pts = np.round(row_tail.values.reshape(-1, 2)[:, None, :]).astype(
                int
            )
            cv2.polylines(
                img, [pts], False, colors["tail"], line_width, line_type
            )

        if timer:
            t = i / fps
            text = f"{t:.2f} s"
            img = cv2.putText(
                img,
                text,
                (64, 64),
                cv2.FONT_HERSHEY_DUPLEX,
                1,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
                False,
            )

        writer.write(img)

    writer.release()
    store.close()
