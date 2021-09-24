from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.interpolate import splev, splprep

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.multi_threshold import MultiThresholdEyeTracker
from ztrack.utils.exception import TrackingError
from ztrack.utils.geometry import wrap_degrees
from ztrack.utils.shape import Points


class BaseFreeSwimTracker(MultiThresholdEyeTracker, ABC):
    @property
    def shapes(self):
        return [
            self._left_eye,
            self._right_eye,
            self._swim_bladder,
            self._points,
        ]

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)
        self._bg = None
        self._is_bg_bright = None
        self._video_path = None
        self._points = Points(np.array([[0, 0]]), 1, "m", symbol="+")

    def calculate_background(self, video_path):
        if self._verbose:
            print("Calculating background...")

        bg = zcv.video_median(video_path, verbose=self._verbose)
        cv2.imwrite(str(Path(video_path).with_suffix(".png")), bg)
        is_bg_bright = cv2.mean(bg)[0] > 127

        return is_bg_bright, bg

    def set_video(self, video_path):
        self._bg = None
        self._video_path = video_path

        if video_path is not None:
            bg_path = Path(video_path).with_suffix(".png")

            if bg_path.exists():
                self._bg = cv2.imread(str(bg_path), 0)
                self._is_bg_bright = cv2.mean(self._bg)[0] > 127

    @staticmethod
    def _interpolate_tail(tail: np.ndarray, n_points: int) -> np.ndarray:
        tck = splprep(tail.T)[0]
        return np.column_stack(splev(np.linspace(0, 1, n_points), tck))

    @classmethod
    def _results_to_series(cls, results):
        eye, tail = results
        eyes_midpoint = eye[:2, :2].mean(0)
        swim_bladder_center = eye[-1, :2]
        midline = eyes_midpoint - swim_bladder_center
        x2, x1 = midline
        heading = np.rad2deg(np.arctan2(x1, x2))
        theta_l, theta_r = eye[:2, -1]
        angle_l = wrap_degrees(theta_l - heading)
        angle_r = wrap_degrees(heading - theta_r)
        s = pd.Series(eye.ravel(), index=cls._index)
        s["left_eye", "angle"] = angle_l
        s["right_eye", "angle"] = angle_r
        s["heading"] = heading

        if tail is not None:
            n_points = len(tail)
            idx = pd.MultiIndex.from_product(
                ((f"point{i:02d}" for i in range(n_points)), ("x", "y"))
            )
            s = pd.concat([s, pd.Series(tail.ravel(), idx)])

        return s

    def annotate_from_series(self, series: pd.Series) -> None:
        ellipse_shapes = [self._left_eye, self._right_eye, self._swim_bladder]
        body_parts = ["left_eye", "right_eye", "swim_bladder"]
        for i, j in zip(ellipse_shapes, body_parts):
            i.visible = True
            s = series[j]
            i.cx, i.cy, i.a, i.b, i.theta = s.cx, s.cy, s.a, s.b, s.theta

        if "point00" in series:
            idx = [f"point{i:02d}" for i in range(self.params.n_points)]
            tail = series.loc[idx].values.reshape(-1, 2)
            self._points.visible = True
            self._points.data = tail
        else:
            self._points.visible = False

    @abstractmethod
    def _track_tail(self, src, point, angle):
        pass

    def _track_img(self, img: np.ndarray):
        if self._bg is None:
            self._is_bg_bright, self._bg = self.calculate_background(
                self._video_path
            )

        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        bg = self._bg[self.roi.to_slice()]

        if self._is_bg_bright:
            img = cv2.subtract(bg, img)
        else:
            img = cv2.subtract(img, bg)

        contours = self._track_contours(img)
        ellipses = self._fit_ellipses(contours)

        centers = ellipses[:, :2]
        sb_center = centers[2]
        midpoint = centers[:2].mean(0)
        midline = sb_center - midpoint
        opp_heading = np.arctan2(*midline[::-1])
        sb_theta = np.deg2rad(ellipses[2, -1])
        sb_posterior = np.round(
            sb_center
            - ellipses[2, 2] * np.array([np.cos(sb_theta), np.sin(sb_theta)])
        ).astype(int)

        try:
            tail = self._track_tail(img, sb_posterior, opp_heading)
        except TrackingError:
            tail = None

        return ellipses, tail
