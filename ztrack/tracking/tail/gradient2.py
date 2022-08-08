from typing import Type

import numpy as np
import pandas as pd
from scipy.ndimage._filters import _gaussian_kernel1d, correlate1d  # noqa

import ztrack.utils.cv as zcv
from ztrack.tracking.tracker import Params, Tracker
from ztrack.utils.shape import Line, Points
from ztrack.utils.variable import Angle, Float, Int, Point


def _track_img(
    img: np.ndarray,
    h,
    w,
    angle_rad,
    tail_base,
    sigma,
    invert,
    n_segments,
    r,
    half_lengths,
    lengths,
    weights,
    roi=None,
):
    x, y = tail_base

    if roi is not None:
        x0, y0 = roi[:2]
        x -= x0
        y -= y0

    if invert:
        img = zcv.rgb2gray_dark_bg_blur(img, sigma, invert)

    results = np.empty(n_segments)

    for i in range(n_segments):
        sin = np.sin(angle_rad)
        cos = np.cos(angle_rad)

        half_length = half_lengths[i]
        length = lengths[i]
        x0 = x + (r_cos := r * cos) - (l_sin := half_length * sin)
        x1 = x + r_cos + l_sin
        y0 = y + (r_sin := r * sin) + (l_cos := half_length * cos)
        y1 = y + r_sin - l_cos

        if min(x0, x1, y0, y1) >= 0 and max(x0, x1) < w and max(y0, y1) < h:
            x_ = np.linspace(x0, x1, length).astype(int)
            y_ = np.linspace(y0, y1, length).astype(int)

            z = img[y_, x_]
            z = correlate1d(
                z.astype(float), weights, 0, mode="nearest", origin=0
            )
            m = length // 2
            argmax = (z[:m].argmax() + m + z[m:].argmin()) // 2
            angle_rad = np.arctan2(y_[argmax] - y, x_[argmax] - x)
            x += round(r * np.cos(angle_rad))
            y += round(r * np.sin(angle_rad))
            results[i] = angle_rad
        else:
            results[i:] = np.nan

    return results


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
        return pd.DataFrame(results)

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

                lw = int(4.0 * float(sigma_tail) + 0.5)
                weights = _gaussian_kernel1d(sigma_tail, 1, lw)[::-1]
                z = correlate1d(
                    z.astype(float), weights, 0, mode="nearest", origin=0
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

    def track_video(self, video_path, ignore_errors=False):
        from decord import VideoReader
        from tqdm import tqdm

        self.set_video(video_path)

        video_reader = VideoReader(str(video_path))

        p = self.params
        h, w = video_reader[0].shape[:2]
        angle_rad = np.deg2rad(p.angle)
        tail_base = p.tail_base
        sigma = p.sigma
        invert = p.invert
        n_segments = p.n_segments
        r = p.segment_length
        half_lengths = np.linspace(p.w1, p.w2, n_segments)
        lengths = (half_lengths * 2).astype(int)
        sigma_tail = p.sigma_tail
        roi = self.roi.value

        it = (
            tqdm(range(len(video_reader)))
            if self._verbose
            else range(len(video_reader))
        )

        s_ = self.roi.to_slice()

        lw = int(4.0 * float(sigma_tail) + 0.5)
        weights = _gaussian_kernel1d(sigma_tail, 1, lw)[::-1]

        data = np.asarray(
            [
                _track_img(
                    video_reader[i].asnumpy()[s_],
                    h,
                    w,
                    angle_rad,
                    tail_base,
                    sigma,
                    invert,
                    n_segments,
                    r,
                    half_lengths,
                    lengths,
                    weights,
                    roi,
                )
                for i in it
            ]
        )

        return self._results_to_dataframe(
            self._transform_from_roi_to_frame(data)
        )
