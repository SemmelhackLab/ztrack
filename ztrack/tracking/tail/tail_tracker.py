from abc import ABC

import numpy as np

from ztrack.tracking.params import Params
from ztrack.tracking.tracker import Tracker


class TailParams(Params):
    pass


class TailTracker(Tracker, ABC):
    @property
    def shapes(self):
        return []

    def _annotate_img(self, img):
        pass

    def _transform_from_roi_to_frame(self, results):
        raise NotImplementedError

    def _track_img(self, img: np.ndarray):
        raise NotImplementedError

    @classmethod
    def _results_to_series(cls, results):
        raise NotImplementedError
