from pathlib import Path
from typing import Type

import cv2
import numpy as np
import pandas as pd

import ztrack.utils.cv as zcv
from ztrack.tracking.mixins.background import BackgroundSubtractionMixin
from ztrack.utils.shape import Points
from ztrack.utils.variable import Float, Int

from ..params import Params
from ..tracker import Tracker


class ParameciaTracker(Tracker, BackgroundSubtractionMixin):
    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params=params)
            self.sigma = Float("Sigma (px)", 0, 0, 100, 0.1)
            self.block_size = Int("Block size", 99, 3, 200)
            self.c = Int("C", -5, -100, 100)
            self.min_area = Int("Min area", 0, 0, 100)
            self.max_area = Int("Max area", 20, 0, 100)

    def __init__(self, roi=None, params: dict = None, *, verbose=0, debug=False):
        super().__init__(roi, params, verbose=verbose, debug=debug)
        self._bg = None
        self._is_bg_bright = False
        self._video_path = None
        self._points = Points(np.array([[0, 0]]), 1, "g", symbol="+")

    @property
    def _Params(self) -> Type[Params]:
        return self.__Params

    @property
    def shapes(self):
        return [self._points]

    def annotate_from_series(self, s: pd.Series) -> None:
        centers = s.values.reshape(-1, 2)
        self._points.visible = True
        self._points.data = centers

    @staticmethod
    def name():
        return "paramecia"

    @staticmethod
    def display_name():
        return "Paramecia"

    @classmethod
    def _results_to_series(cls, results):
        row = results.ravel()
        return pd.Series(row)

    def set_video(self, video_path):
        self._bg = None
        self._video_path = video_path

        if video_path is not None:
            bg_path = Path(video_path).with_suffix(".png")

            if bg_path.exists():
                self._bg = cv2.imread(str(bg_path), 0)
                self._is_bg_bright = cv2.mean(self._bg)[0] > 127

    def _transform_from_roi_to_frame(self, results: np.ndarray):
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            results += (x0, y0)
        return results

    def _track_img(self, img: np.ndarray):
        if self._bg is None:
            self._is_bg_bright, self._bg = self.calculate_background(
                self._video_path
            )

        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        bg = self._bg[self.roi.to_slice()]

        if self._is_bg_bright:
            img = cv2.subtract(bg, img)
        else:
            img = cv2.subtract(img, bg)

        p = self.params

        img = zcv.gaussian_blur(img, p.sigma)
        img_thresh = zcv.adaptive_threshold(img, p.block_size, p.c)
        contours = zcv.find_contours(img_thresh)
        contours = list(
            filter(
                lambda x: p.min_area <= cv2.contourArea(x) < p.max_area,
                contours,
            )
        )
        centers = np.array(
            [zcv.contour_center(contour) for contour in contours]
        )

        return centers
