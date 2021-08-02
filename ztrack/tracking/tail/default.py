import cv2
import numpy as np

from skimage.draw import circle_perimeter

from ztrack.utils.variable import Float, Point, Int
from ztrack.utils.geometry import angle_diff
from ztrack.utils.math import split_int

from .tail_tracker import TailParams, TailTracker


class DefaultTailTracker(TailTracker):
    class __Params(TailParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma", 0, 0, 100, 0.1)
            self.n_steps = Int("Number of steps", 10, 3, 20)
            self.n_points = Int("Number of points", 51, 0, 99)
            self.tail_base = Point("Tail base", (250, 120))
            self.length = Int("Tail length", 200, 0, 1000)
            self.angle = Float("Angle", np.pi / 2, -np.pi, np.pi, np.pi / 180)
            self.theta = Float("Theta", np.pi / 6, 0, np.pi, np.pi / 180)

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def _preprocess(img, sigma=0):
        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        if cv2.mean(img)[0] > 127:
            img = cv2.bitwise_not(img)

        if sigma > 0:
            img = cv2.GaussianBlur(img, (0, 0), sigma)

        return img

    def _track_tail(self, img):
        x, y = self.params.tail_base
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            point = (x - x0, y - y0)
        else:
            point = (x, y)
        angle = self.params.angle
        img = self._preprocess(img, self.params.sigma)
        h, w = img.shape
        tail = np.zeros((self.params.n_steps + 1, 2), dtype=int)
        tail[0] = point
        step_lengths = split_int(round(self.params.length), self.params.n_steps)
        for i in range(self.params.n_steps):
            points = np.column_stack(circle_perimeter(*point, step_lengths[i], shape=(w, h)))
            angles = np.arctan2(*reversed((points - point).T))
            idx = angle_diff(angles, angle) < self.params.theta
            points, angles = points[idx], angles[idx]
            x, y = points.T
            argmax = img[y, x].argmax()
            angle = angles[argmax]
            tail[i + 1] = point = points[argmax]
        return tail

    @staticmethod
    def name():
        return "default"

    @staticmethod
    def display_name():
        return "Default"
