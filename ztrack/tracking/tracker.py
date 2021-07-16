from abc import ABC, abstractmethod

import numpy as np
import pandas as pd
from ztrack.utils.roi import normalize_roi, roi2slice


class Tracker(ABC):
    def __init__(self):
        self._roi = None

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, roi):
        self._roi = normalize_roi(roi)

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def display_name(self):
        pass

    @abstractmethod
    def _track_region(self, img) -> pd.Series:
        pass

    def _track_frame(self, frame: np.ndarray) -> pd.Series:
        img = frame[roi2slice(self.roi)]
        return self._track_region(img)

    def track_frames(self, frames: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame([self._track_frame(frame) for frame in frames])
