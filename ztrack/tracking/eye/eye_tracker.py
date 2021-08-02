from abc import ABC, abstractmethod

import cv2
import numpy as np
import pandas as pd

from ztrack.tracking.params import Params
from ztrack.tracking.tracker import Tracker
from ztrack.utils.cv import binary_threshold, find_contours
from ztrack.utils.geometry import wrap_degrees
from ztrack.utils.shape import Ellipse


class EyeParams(Params, ABC):
    pass


class EyeTracker(Tracker, ABC):
    _index = pd.MultiIndex.from_product(
        (
            ("left_eye", "right_eye", "swim_bladder"),
            ("cx", "cy", "a", "b", "theta"),
        )
    )

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)
        self._left_eye = Ellipse(0, 0, 1, 1, 0, 4, "b")
        self._right_eye = Ellipse(0, 0, 1, 1, 0, 4, "r")
        self._swim_bladder = Ellipse(0, 0, 1, 1, 0, 4, "g")

    @property
    def shapes(self):
        return [self._left_eye, self._right_eye, self._swim_bladder]

    @abstractmethod
    def _track_ellipses(self, src: np.ndarray) -> np.ndarray:
        pass

    @staticmethod
    def _preprocess(img, sigma=0):
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        if cv2.mean(img)[0] > 127:
            img = cv2.bitwise_not(img)

        if sigma > 0:
            img = cv2.GaussianBlur(img, (0, 0), sigma)

        return img

    @staticmethod
    def _binary_segmentation(img, threshold):
        return find_contours(binary_threshold(img, threshold))

    @staticmethod
    def _correct_orientation(ellipses):
        centers = ellipses[:, :2]
        midpoint = centers[:2].mean(0)
        midline = midpoint - centers[2]
        heading = np.rad2deg(np.arctan2(*midline[::-1]))
        is_opposite = abs(wrap_degrees(heading - ellipses[:, -1])) > 90
        ellipses[is_opposite, -1] = wrap_degrees(
            ellipses[is_opposite, -1] - 180
        )
        return ellipses

    @staticmethod
    def _fit_ellipses(contours):
        ellipses = np.array(
            [
                (x, y, b / 2, a / 2, theta - 90)
                for (x, y), (a, b), theta in map(
                    cv2.fitEllipse, map(cv2.convexHull, contours)
                )
            ]
        )

        return ellipses

    @staticmethod
    def _sort_centers(centers):
        idx = np.arange(3)
        swim_bladder = np.argmin(
            [np.linalg.norm(np.subtract(*centers[idx != i])) for i in idx]
        )
        eyes = idx[idx != swim_bladder]
        left_eye, right_eye = (
            eyes
            if np.cross(*centers[eyes] - centers[swim_bladder]) > 0
            else eyes[::-1]
        )
        return left_eye, right_eye, swim_bladder

    def annotate_from_series(self, series: pd.Series) -> None:
        ellipse_shapes = [self._left_eye, self._right_eye, self._swim_bladder]
        body_parts = ["left_eye", "right_eye", "swim_bladder"]
        for i, j in zip(ellipse_shapes, body_parts):
            i.visible = True
            s = series[j]
            i.cx, i.cy, i.a, i.b, i.theta = s.cx, s.cy, s.a, s.b, s.theta

    def _track_img(self, img: np.ndarray) -> np.ndarray:
        return self._track_ellipses(img)

    def _transform_from_roi_to_frame(self, results: np.ndarray):
        if self.roi.value is not None:
            results[:, :2] += self.roi.value[:2]
        return results

    @classmethod
    def _results_to_series(cls, results: np.ndarray):
        eyes_midpoint = results[:2, :2].mean(0)
        swim_bladder_center = results[-1, :2]
        midline = eyes_midpoint - swim_bladder_center
        x2, x1 = midline
        heading = np.rad2deg(np.arctan2(x1, x2))
        theta_l, theta_r = results[:2, -1]
        angle_l = wrap_degrees(theta_l - heading)
        angle_r = wrap_degrees(heading - theta_r)
        s = pd.Series(results.ravel(), index=cls._index)
        s["left_eye", "angle"] = angle_l
        s["right_eye", "angle"] = angle_r
        s["heading"] = heading
        return s
