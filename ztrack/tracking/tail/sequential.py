import numpy as np

import ztrack.utils.cv as zcv
from ztrack.utils.variable import Angle, Float, Int, Point, Rect, String
from ztrack.utils.shape import Rectangle

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
            self.fraction = Float("Fraction", .5, 0, 1, .05)
            self.bbox_l_tail = Rect("Left tail", (0, 0, 30, 30))
            self.bbox_r_tail = Rect("Right tail", (0, 0, 30, 30))
            self.step_lengths = String("Step lengths", "")

    def __init__(self, roi=None, params: dict = None, *, verbose=0, debug=False):
        super().__init__(roi, params, verbose=verbose, debug=debug)

        self._left_tail_bbox = Rectangle(0, 0, 1, 1, 4, "b")
        self._right_tail_bbox = Rectangle(0, 0, 1, 1, 4, "r")
        self._bboxes = [self._left_tail_bbox, self._right_tail_bbox]

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
        img = zcv.rgb2gray_dark_bg_blur(img, p.sigma)

        x, y, w, h = p.bbox_l_tail
        img[y:y+h, x:x+w] = 0

        x, y, w, h = p.bbox_r_tail
        img[y:y+h, x:x+w] = 0

        return zcv.sequential_track_tail(
            img, point, angle, theta, theta2, p.fraction, p.n_steps, p.length,
            p.step_lengths
        )

    @staticmethod
    def name():
        return "sequential"

    @property
    def shapes(self):
        return super().shapes + self._bboxes

    @staticmethod
    def display_name():
        return "Sequential"

    def annotate(self, frame: np.ndarray) -> None:
        super().annotate(frame)

        p = self.params

        for i, j in zip(self._bboxes, (p.bbox_l_tail, p.bbox_r_tail)):
            i.visible = True
            x, y, w, h = j
            x -= self.roi.value[0]
            y -= self.roi.value[1]
            i.x, i.y, i.w, i.h = x, y, w, h
