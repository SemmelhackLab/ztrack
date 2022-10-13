import numpy as np

import ztrack.utils.cv as zcv
from ztrack.utils.variable import Angle, Bool, Float, Int, Point, String

from .tail_tracker import TailParams, TailTracker


class SequentialTailTracker(TailTracker):
    class __Params(TailParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
            self.n_steps = Int("Number of steps", 10, 3, 20)
            self.length = Int("Tail length (px)", 200, 0, 1000)
            self.tail_base = Point("Tail base (x, y)", (250, 120))
            self.angle = Angle("Initial angle (°)", 90)
            self.theta = Angle("Search angle (°)", 60)
            self.theta2 = Angle("Search angle 2 (°)", 60)
            self.fraction = Float("Fraction", 0.5, 0, 1, 0.05)
            self.step_lengths = String("Step lengths", "")
            self.invert = Bool("invert", True)

    def __init__(
        self, roi=None, params: dict = None, *, verbose=0, debug=False
    ):
        super().__init__(roi, params, verbose=verbose, debug=debug)

    @property
    def _Params(self):
        return self.__Params

    def _track_tail(self, img):
        p = self.params

        x, y = p.tail_base
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            point = (x - x0, y - y0)
        else:
            point = (x, y)

        angle = np.deg2rad(p.angle)
        theta = np.deg2rad(p.theta / 2)
        theta2 = np.deg2rad(p.theta2 / 2)
        img = zcv.rgb2gray_dark_bg_blur(img, p.sigma, p.invert)

        return zcv.sequential_track_tail(
            img,
            point,
            angle,
            theta,
            theta2,
            p.fraction,
            p.n_steps,
            p.length,
            p.step_lengths,
        )

    @staticmethod
    def name():
        return "sequential"

    @property
    def shapes(self):
        return super().shapes

    @staticmethod
    def display_name():
        return "Sequential"
