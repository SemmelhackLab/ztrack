from typing import Type

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

import ztrack.utils.cv as zcv
from ztrack.tracking.tracker import Params, Tracker
from ztrack.utils.shape import Points
from ztrack.utils.variable import Angle, Bool, Float, Int, Point


class GradientTailTracker(Tracker):
    @property
    def _Params(self) -> Type[Params]:
        return self.__Params

    @property
    def shapes(self):
        return [self._points]

    def annotate_from_series(self, s: pd.Series) -> None:
        raise NotImplementedError

    @classmethod
    def _results_to_series(cls, results):
        raise NotImplementedError

    def _transform_from_roi_to_frame(self, results):
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            results[:, :2] += (x0, y0)

        return results

    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
            self.n_segments = Int("Number of segments", 10, 3, 20)
            self.segment_length = Int("Segment length (px)", 10, 5, 50)
            self.tail_base = Point("Tail base (x, y)", (250, 120))
            self.angle = Angle("Initial angle (°)", 90)
            self.theta = Angle("Search angle (°)", 60)
            self.d_theta = Float("dtheta", 0.05, 0.01, 0.1, 0.01)
            self.sigma_tail = Float("sigma tail", 0.2, 0.05, 0.4, 0.05)
            self.invert = Bool("invert", True)

    def __init__(
        self,
        roi=None,
        params: dict = None,
        *,
        verbose=0,
        debug=False,
    ):
        super().__init__(roi, params, verbose=verbose, debug=debug)
        self._points = Points(np.array([[0, 0]]), 1, "m", symbol="+")

    @classmethod
    def _results_to_dataframe(cls, results):
        n_segments = results.shape[-2]
        idx = pd.MultiIndex.from_product(
            ((f"point{i:02d}" for i in range(n_segments)), ("x", "y", "angle"))
        )
        return pd.DataFrame(results.reshape(len(results), -1), idx)

    def _track_img(self, img: np.ndarray):
        p = self.params

        x, y = p.tail_base
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            x -= x0
            y -= y0

        angle = np.deg2rad(p.angle)
        theta = np.deg2rad(p.theta / 2)
        img = zcv.rgb2gray_dark_bg_blur(img, p.sigma, p.invert)

        h, w = img.shape
        n_segments = p.n_segments
        results = np.empty((n_segments, 3))
        d_theta = p.d_theta
        r = p.segment_length

        sigma_tail = p.sigma_tail / d_theta

        for i in range(n_segments):
            if x - r < 0 or x + r >= w or y - r < 0 or y + r >= h:
                results[i:] = np.nan
                break

            angles = np.arange(angle - theta, angle + theta, d_theta)
            x_ = (r * np.cos(angles)).astype(int) + x
            y_ = (r * np.sin(angles)).astype(int) + y
            z = img[y_, x_]
            z = gaussian_filter(z.astype(float), sigma_tail, 1, mode="nearest")
            argmax = (z.argmin() + z.argmax()) // 2
            angle = angles[argmax]
            x = x_[argmax]
            y = y_[argmax]
            results[i] = (x, y, angle)

        return results

    @staticmethod
    def name():
        return "gradient"

    @staticmethod
    def display_name():
        return "Gradient"

    def annotate_from_results(self, a: np.ndarray) -> None:
        self._points.visible = True
        self._points.data = a[:, :2]
