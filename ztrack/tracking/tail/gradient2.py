from typing import Type

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

import ztrack.utils.cv as zcv
from ztrack.tracking.tracker import Params, Tracker
from ztrack.utils.shape import Line, Points
from ztrack.utils.variable import Angle, Float, Int, Point


class GradientTailTracker2(Tracker):
    @property
    def _Params(self) -> Type[Params]:
        return self.__Params

    @property
    def shapes(self):
        return [self._points, self._line1, self._line2]

    def annotate_from_series(self, s: pd.Series) -> None:
        raise NotImplementedError

    @classmethod
    def _results_to_series(cls, results):
        raise NotImplementedError

    def _transform_from_roi_to_frame(self, results):
        # if self.roi.value is not None:
        #     x0, y0 = self.roi.value[:2]
        #     results[:, :2] += (x0, y0)
        return results

    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
            self.n_segments = Int("Number of segments", 10, 3, 20)
            self.segment_length = Int("Segment length (px)", 10, 5, 50)
            self.tail_base = Point("Tail base (x, y)", (250, 120))
            self.angle = Angle("Initial angle (°)", 90)
            self.w1 = Int("Tail base width (px)", 30, 5, 100)
            self.w2 = Int("Tail end width (px)", 30, 5, 100)
            self.sigma_tail = Float("sigma tail", 1, 0, 10, 0.1)
            self.invert = Int("invert", 0, -1, 1)

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
        self._line1 = Line(0, 0, 0, 0, 1, "m")
        self._line2 = Line(0, 0, 0, 0, 1, "m")

    @classmethod
    def _results_to_dataframe(cls, results):
        return pd.DataFrame(results[:, :, -1])

    def _track_img(self, img: np.ndarray):
        p = self.params

        x, y = p.tail_base
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            x -= x0
            y -= y0

        angle = np.deg2rad(p.angle)
        if p.invert:
            img = zcv.rgb2gray_dark_bg_blur(img, p.sigma, p.invert)

        h, w = img.shape
        n_segments = p.n_segments
        results = np.empty((n_segments, 3))
        r = p.segment_length
        w1 = p.w1
        w2 = p.w2
        half_lengths = np.linspace(w1, w2, n_segments)
        lengths = (half_lengths * 2).astype(int)
        sigma_tail = p.sigma_tail

        for i in range(n_segments):
            sin = np.sin(angle)
            cos = np.cos(angle)

            half_length = half_lengths[i]
            length = lengths[i]
            x0 = x + (r_cos := r * cos) - (l_sin := half_length * sin)
            x1 = x + r_cos + l_sin
            y0 = y + (r_sin := r * sin) + (l_cos := half_length * cos)
            y1 = y + r_sin - l_cos

            if min(x0, x1, y0, y1) >= 0 and max(x0, x1, y0, y1) < w:
                x_ = np.linspace(x0, x1, length).astype(int)
                y_ = np.linspace(y0, y1, length).astype(int)

                z = img[y_, x_]
                z = gaussian_filter1d(
                    z.astype(float), sigma_tail, 0, 1, mode="nearest"
                )
                m = length // 2
                argmax = (z[:m].argmax() + m + z[m:].argmin()) // 2
                angle = np.arctan2(y_[argmax] - y, x_[argmax] - x)
                x += round(r * np.cos(angle))
                y += round(r * np.sin(angle))
                results[i] = (x, y, angle)
            else:
                results[i:] = np.nan

        return results

    @staticmethod
    def name():
        return "gradient2"

    @staticmethod
    def display_name():
        return "Gradient2"

    def annotate_from_results(self, a: np.ndarray) -> None:
        self._points.visible = True
        self._points.data = a[:, :2]
        self._line1.set_center_length_angle(
            a[0, :2], self.params.w1, a[0, -1] + np.pi / 2
        )
        self._line2.set_center_length_angle(
            a[-1, :2], self.params.w2, a[-1, -1] + np.pi / 2
        )
