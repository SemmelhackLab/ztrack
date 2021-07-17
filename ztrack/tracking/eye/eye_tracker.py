from abc import ABC, abstractmethod

import cv2
import numpy as np

from ztrack.tracking.params import Params
from ztrack.tracking.tracker import Tracker
from ztrack.utils.cv import binary_threshold, find_contours
from ztrack.utils.geometry import wrap_degrees
from ztrack.utils.shape import Ellipse


class EyeParams(Params):
    pass


class EyeTracker(Tracker, ABC):
    def __init__(self):
        super().__init__()
        self._left_eye = Ellipse(0, 0, 1, 1, 0)
        self._right_eye = Ellipse(0, 0, 1, 1, 0)
        self._swim_bladder = Ellipse(0, 0, 1, 1, 0)

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

    def annotate(self, img: np.ndarray):
        ellipse_shapes = [self._left_eye, self._right_eye, self._swim_bladder]
        ellipses = self._track_ellipses(img)
        for i, j in zip(ellipse_shapes, ellipses):
            i.cx, i.cy, i.a, i.b, i.theta = j
