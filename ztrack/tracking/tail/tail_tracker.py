from abc import ABC, abstractmethod
from typing import Union

import numpy as np
import pandas as pd
from matplotlib import cm, colors

from ztrack.tracking.params import Params
from ztrack.tracking.tracker import Tracker
from ztrack.utils.shape import Points


class TailParams(Params):
    pass


class TailTracker(Tracker, ABC):
    max_n_points = 99

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
    def _results_to_dataframe(cls, results: np.ndarray):
        n_points = len(results)
        idx = pd.MultiIndex.from_product(
            ((f"point{i:02d}" for i in range(n_points)), ("x", "y"))
        )
        return pd.DataFrame(results.reshape(len(results), -1), columns=idx)

    @abstractmethod
    def _track_tail(self, img: np.ndarray):
        pass

    def _track_img(self, img: np.ndarray):
        tail = self._track_tail(img)
        return tail

    @property
    def shapes(self):
        return [self._points]

    def annotate_from_results(self, a: np.ndarray) -> None:
        self._points.visible = True
        self._points.data = a

    def annotate_from_series(self, s: pd.Series) -> None:
        tail = s.values.reshape(-1, 2)
        self._points.visible = True
        self._points.data = tail

    def _transform_from_roi_to_frame(self, results: np.ndarray):
        if self.roi.value is not None:
            x0, y0 = self.roi.value[:2]
            results += (x0, y0)
        return results
