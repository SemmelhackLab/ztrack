from typing import Type

import numpy as np
import pandas as pd

from ztrack.tracking.mixins.background import BackgroundSubtractionMixin
from ztrack.utils.variable import Float, Int, UInt8

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
            self.max_area = Int("Max area", 0, 20, 100)

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi=roi, params=params, verbose=verbose)

    @property
    def _Params(self) -> Type[Params]:
        return self.__Params

    @property
    def shapes(self):
        return []

    def annotate_from_series(self, s: pd.Series) -> None:
        pass

    @staticmethod
    def name():
        return "paramecia"

    @staticmethod
    def display_name():
        return "Paramecia"

    @classmethod
    def _results_to_series(cls, results):
        return pd.Series([])

    def _transform_from_roi_to_frame(self, results):
        return results

    def _track_img(self, img: np.ndarray):
        return None
