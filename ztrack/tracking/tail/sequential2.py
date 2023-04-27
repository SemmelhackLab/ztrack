from typing import Type

import numpy as np
import pandas as pd
from scipy.ndimage._filters import _gaussian_kernel1d, correlate1d  # noqa

import ztrack.utils.cv as zcv
from ztrack.tracking.tracker import Params, Tracker
from ztrack.utils.math import split_int
from ztrack.utils.shape import Line, Points
from ztrack.utils.variable import Angle, Bool, Float, Int, Point


def _track_img(
    img: np.ndarray,
    h,
    w,
    angle_rad,
    tail_base,
    sigma,
    invert,
    n_segments,
    segment_lenths,
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

    results = np.empty((n_segments, 2), dtype=np.int16)

    for i in range(n_segments):
        sin = np.sin(angle_rad)
        cos = np.cos(angle_rad)

        r = segment_lenths[i]
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

            argmax = z.argmax()

            xn = x_[argmax]
            yn = y_[argmax]

            dx = xn - x
            dy = yn - y

            s = np.sqrt(dx * dx + dy * dy)
            x = x + dx / s * r
            y = y + dy / s * r

            results[i] = x, y
        else:
            results[i:] = -1

    return results


class Sequential2(Tracker):
    @property
    def _Params(self) -> Type[Params]:
        return self.__Params

    @property
    def shapes(self):
        return [self._points, self._line1, self._line2]

    def annotate_from_series(self, s: pd.Series) -> None:
        tail = s.values.reshape(-1, 2)
        self._points.visible = True
        self._points.data = tail

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
            self.tail_length = Int("Tail length (px)", 200, 0, 500)
            self.tail_base = Point("Tail base (x, y)", (250, 120))
            self.angle = Angle("Initial angle (°)", 90)
            self.w1 = Int("Tail base width (px)", 30, 5, 100)
            self.w2 = Int("Tail end width (px)", 30, 5, 100)
            self.sigma_tail = Float("sigma tail", 1, 0, 10, 0.1)
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
        self._line1 = Line(0, 0, 0, 0, 1, "m")
        self._line2 = Line(0, 0, 0, 0, 1, "m")

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
        results = np.empty((n_segments, 2), dtype=np.int16)

        segment_lengths = split_int(p.tail_length, n_segments)
        w1 = p.w1
        w2 = p.w2
        half_lengths = (
            w1
            + (w2 - w1)
            * np.cumsum((0, *segment_lengths[1:]))
            / segment_lengths[1:].sum()
        )
        lengths = (half_lengths * 2).astype(int)
        sigma_tail = p.sigma_tail

        for i in range(n_segments):
            r = segment_lengths[i]
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
                weights = _gaussian_kernel1d(sigma_tail, 0, lw)[::-1]
                z = correlate1d(
                    z.astype(float), weights, 0, mode="nearest", origin=0
                )

                argmax = z.argmax()

                xn = x_[argmax]
                yn = y_[argmax]

                dx = xn - x
                dy = yn - y

                s = np.sqrt(dx * dx + dy * dy)
                x = x + dx / s * r
                y = y + dy / s * r

                results[i] = x, y
            else:
                results[i:] = -1

        return results

    @staticmethod
    def name():
        return "sequential2"

    @staticmethod
    def display_name():
        return "Sequential2"

    @staticmethod
    def calculate_angle(p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        return np.arctan2(x1 - x2, y2 - y1)

    def annotate_from_results(self, a: np.ndarray) -> None:
        self._points.visible = True

        self._points.data = np.row_stack((self.params.tail_base, a))

        angle1 = self.calculate_angle(self.params.tail_base, a[0])
        angle2 = self.calculate_angle(a[-2], a[-1])
        self._line1.set_center_length_angle(a[0], self.params.w1, angle1)
        self._line2.set_center_length_angle(a[-1], self.params.w2, angle2)
        self._line1.visible = True
        self._line2.visible = True

    @classmethod
    def _results_to_dataframe(cls, results):
        n_points = results.shape[-2]
        idx = pd.MultiIndex.from_product(
            ((f"point{i:02d}" for i in range(n_points)), ("x", "y"))
        )
        return pd.DataFrame(results.reshape(len(results), -1), columns=idx)

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

        segment_lengths = split_int(p.tail_length, n_segments)
        half_lengths = (
            p.w1
            + (p.w2 - p.w1)
            * np.cumsum((0, *segment_lengths[1:]))
            / segment_lengths[1:].sum()
        )
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
                    segment_lengths,
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
