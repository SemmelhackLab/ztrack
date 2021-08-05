from abc import ABC, abstractmethod
from typing import Union

import numpy as np
import pandas as pd
from matplotlib import cm, colors
from scipy.interpolate import splev, splprep

from ztrack.tracking.params import Params
from ztrack.tracking.tracker import Tracker
from ztrack.utils.shape import Points


class TailParams(Params):
    pass


class TailTracker(Tracker, ABC):
    max_n_points = 100

    def __init__(
        self,
        roi=None,
        params: dict = None,
        *,
        verbose=0,
        cmap: Union[colors.Colormap, str] = "jet",
    ):
        super().__init__(roi, params, verbose=verbose)

        self._tail_cmap = cm.get_cmap(cmap)
        self._points = Points(np.array([[0, 0]]), 1, "m", symbol="+")

    @classmethod
    def _results_to_series(cls, results: np.ndarray):
        n_points = len(results)
        idx = pd.MultiIndex.from_product(
            ((f"point{i:02d}" for i in range(n_points)), ("x", "y"))
        )
        return pd.Series(results.ravel(), idx)

    @abstractmethod
    def _track_tail(self, img: np.ndarray):
        pass

    @staticmethod
    def _interpolate_tail(tail: np.ndarray, n_points: int) -> np.ndarray:
        tck = splprep(tail.T)[0]
        return np.column_stack(splev(np.linspace(0, 1, n_points), tck))

    def _track_img(self, img: np.ndarray):
        tail = self._track_tail(img)
        return self._interpolate_tail(tail, self.params.n_points)

    @property
    def shapes(self):
        return [self._points]

    def annotate_from_series(self, s: pd.Series) -> None:
        tail = s.values.reshape(-1, 2)
        self._points.visible = True
        self._points.data = tail

    def _transform_from_roi_to_frame(self, results: np.ndarray):
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            results += (x0, y0) * self.params.n_points
        return results
