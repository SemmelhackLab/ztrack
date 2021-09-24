import cv2
import numpy as np
from skimage.draw import circle_perimeter

from ztrack.tracking.params import Params
from ztrack.utils.exception import TrackingError
from ztrack.utils.geometry import angle_diff
from ztrack.utils.math import split_int
from ztrack.utils.variable import Angle, Float, Int, UInt8

from .base import BaseFreeSwimTracker


class SequentialFreeSwimTracker(BaseFreeSwimTracker):
    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma_eye = Float("Eye sigma (px)", 0, 0, 100, 0.1)
            self.sigma_tail = Float("Tail sigma (px)", 0, 0, 100, 0.1)
            self.threshold_segmentation = UInt8("Segmentation threshold", 70)
            self.threshold_left_eye = UInt8("Left eye threshold", 70)
            self.threshold_right_eye = UInt8("Right eye threshold", 70)
            self.threshold_swim_bladder = UInt8("Swim bladder threshold", 70)
            self.n_steps = Int("Number of steps", 20, 3, 20)
            self.n_points = Int("Number of points", 51, 2, 100)
            self.length = Int("Tail length (px)", 90, 0, 1000)
            self.theta = Angle("Search angle (°)", 60)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "sequential"

    @staticmethod
    def display_name():
        return "Sequential"

    def _track_tail(self, src, point, angle):
        theta = np.deg2rad(self.params.theta / 2)

        if self.params.sigma_eye > 0:
            img = cv2.GaussianBlur(src, (0, 0), self.params.sigma_eye)
        else:
            img = src

        h, w = img.shape
        tail = np.zeros((self.params.n_steps + 1, 2), dtype=int)
        tail[0] = point
        step_lengths = split_int(
            round(self.params.length), self.params.n_steps
        )
        for i in range(self.params.n_steps):
            points = np.column_stack(
                circle_perimeter(*point, step_lengths[i], shape=(w, h))
            )
            angles = np.arctan2(*reversed((points - point).T))
            idx = angle_diff(angles, angle) < theta
            points, angles = points[idx], angles[idx]
            x, y = points.T

            try:
                argmax = img[y, x].argmax()
            except ValueError:
                raise TrackingError("Tail tracking failed")

            angle = angles[argmax]
            tail[i + 1] = point = points[argmax]

        return self._interpolate_tail(tail, self.params.n_points)
