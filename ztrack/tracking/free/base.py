from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

# from ztrack.tracking.eye.multi_threshold import MultiThresholdEyeTracker
from ztrack.tracking.eye.eye_tracker import EyeTracker
from ztrack.tracking.tail.tail_tracker import TailTracker

# from ztrack.tracking.mixins.background import BackgroundSubtractionMixin
from ztrack.tracking.tracker import Tracker
from ztrack.utils import cv as zcv
from ztrack.utils.exception import TrackingError
from ztrack.utils.shape import Circle, Ellipse, Points


class BaseFreeSwimTracker(Tracker):
    @property
    def shapes(self):
        return [
            self._left_eye,
            self._right_eye,
            self._swim_bladder,
            self._points,
            self._arena,
        ]

    def __init__(self, roi=None, params: dict = None, *, verbose=0, debug=False):
        super().__init__(roi, verbose=verbose, debug=debug)
        self._params = self._Params(params)
        self._bg = None
        self._video_path = None

        self._left_eye = Ellipse(0, 0, 1, 1, 0, 4, "b")
        self._right_eye = Ellipse(0, 0, 1, 1, 0, 4, "r")
        self._swim_bladder = Ellipse(0, 0, 1, 1, 0, 4, "g")

        self._points = Points(np.array([[0, 0]]), 1, "m", symbol="+")
        self._arena = Circle(0, 0, 1, 2, "c")

    def set_video(self, video_path):
        self._bg = None
        self._video_path = video_path

        if video_path is not None:
            bg_path = Path(video_path).with_suffix(".png")

            if bg_path.exists():
                self._bg = cv2.imread(str(bg_path), 0)
                self._is_bg_bright = cv2.mean(self._bg)[0] > 127

    @classmethod
    def _results_to_series(cls, results):
        eye = results[:15].reshape((3, 5))
        tail = results[15:].reshape((-1, 2))

        s = EyeTracker._results_to_series(eye)
        t = TailTracker._results_to_series(tail)

        return pd.concat([s, t])

    def annotate_from_series(self, series: pd.Series) -> None:
        EyeTracker.annotate_from_series(self, series.iloc[:15])
        TailTracker.annotate_from_series(self, series.iloc[18:])

    def annotate_from_results(self, a) -> None:
        eye = a[:15].reshape((3, 5))
        tail = a[15:].reshape((-1, 2))
        EyeTracker.annotate_from_results(self, eye)
        TailTracker.annotate_from_results(self, tail)
        self._arena.visible = True
        self._arena.cx = self.params.cx
        self._arena.cy = self.params.cy
        self._arena.r = self.params.r

    def _transform_from_roi_to_frame(self, results):
        n_frames = len(results)
        eye = results[:, :15].reshape((n_frames, 3, 5))
        tail = results[:, 15:].reshape((n_frames, -1, 2))
        eye = EyeTracker._transform_from_roi_to_frame(self, eye)
        tail = TailTracker._transform_from_roi_to_frame(self, tail)
        return np.column_stack((eye.reshape((n_frames, -1)), tail.reshape((n_frames, -1))))

    def get_mask(self, img):
        p = self.params
        return cv2.circle(np.zeros_like(img.copy(), np.uint8), (p.cx, p.cy), p.r, 1, -1)

    @abstractmethod
    def _track_tail(self, src, point, angle):
        pass

    @abstractmethod
    def _track_eyes(self, img):
        pass

    @abstractmethod
    def _track_img(self, img: np.ndarray):
        pass
