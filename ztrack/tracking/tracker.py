from abc import ABC, abstractmethod
from typing import Type

import numpy as np
import pandas as pd
from decord import VideoReader
from tqdm import tqdm

from ztrack.utils.variable import Rect

from .params import Params


class Tracker(ABC):
    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        self._roi = Rect("", roi)
        self._params = self._Params(params)
        self._verbose = verbose

    def __repr__(self):
        return f"{self.__class__.__name__}(roi={self._roi.value}, params={self.params.to_dict()})"

    @property
    @abstractmethod
    def _Params(self) -> Type[Params]:
        pass

    def _get_bbox_img(self, frame: np.ndarray):
        return frame[self._roi.to_slice()]

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, bbox):
        self._roi = bbox

    @property
    @abstractmethod
    def shapes(self):
        pass

    def annotate(self, frame: np.ndarray) -> None:
        return self._annotate_img(self._get_bbox_img(frame))

    @abstractmethod
    def annotate_from_series(self, s: pd.Series) -> None:
        pass

    @abstractmethod
    def _annotate_img(self, img: np.ndarray) -> None:
        pass

    @property
    def params(self) -> Params:
        return self._params

    @staticmethod
    @abstractmethod
    def name():
        pass

    @staticmethod
    @abstractmethod
    def display_name():
        pass

    def _track_frame(self, frame: np.ndarray) -> pd.Series:
        results = self._track_img(frame[self.roi.to_slice()])
        return self._results_to_series(
            self._transform_from_roi_to_frame(results)
        )

    @classmethod
    @abstractmethod
    def _results_to_series(cls, results):
        pass

    @abstractmethod
    def _transform_from_roi_to_frame(self, results):
        pass

    @abstractmethod
    def _track_img(self, img: np.ndarray):
        pass

    def track_video(self, video_path):
        video_reader = VideoReader(str(video_path))
        it = (
            tqdm(range(len(video_reader)))
            if self._verbose
            else range(len(video_reader))
        )
        return pd.DataFrame(
            [self._track_frame(video_reader[i].asnumpy()) for i in it]
        )
