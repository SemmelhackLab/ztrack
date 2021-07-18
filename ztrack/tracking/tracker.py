from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from .params import Params
from .variable import BBox


class Tracker(ABC):
    def __init__(self):
        self._bbox = BBox("")

    def _get_bbox_img(self, frame: np.ndarray):
        return frame[self._bbox.to_slice()]

    @property
    def bbox(self):
        return self._bbox

    @bbox.setter
    def bbox(self, bbox):
        self._bbox = bbox

    @property
    @abstractmethod
    def shapes(self):
        pass

    def annotate(self, frame: np.ndarray) -> None:
        return self._annotate_img(self._get_bbox_img(frame))

    @abstractmethod
    def _annotate_img(self, img: np.ndarray) -> None:
        pass

    @property
    @abstractmethod
    def params(self) -> Params:
        pass

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def display_name(self):
        pass

    @abstractmethod
    def _track_frame(self, frame: np.ndarray) -> pd.Series:
        pass

    def track_frames(self, frames: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame([self._track_frame(frame) for frame in frames])
