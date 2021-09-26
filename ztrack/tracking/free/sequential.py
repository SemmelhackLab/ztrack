import numpy as np

import ztrack.utils.cv as zcv
from ztrack.tracking.params import Params
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
        p = self.params
        theta = np.deg2rad(p.theta / 2)
        img = zcv.gaussian_blur(src, p.sigma_tail)
        tail = zcv.sequential_track_tail(
            img, point, angle, theta, p.n_steps, p.length, p.n_points
        )

        return tail
