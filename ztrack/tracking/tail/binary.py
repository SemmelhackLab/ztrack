import numpy as np
import pandas as pd

from ztrack.utils.variable import Float, UInt8

from .tail_tracker import TailParams, TailTracker


class BinaryTailTracker(TailTracker):
    class __Params(TailParams):
        def __init__(self):
            super().__init__()
            self.sigma = Float("Sigma", 0, 0, 100, 0.1)
            self.threshold = UInt8("Threshold", 127)

    def __init__(self, params: dict = None):
        super().__init__(params)

    @property
    def _Params(self):
        return self.__Params

    @property
    def name(self):
        return "binary"

    @property
    def display_name(self):
        return "Binary threshold"

    def _track_frame(self, frame: np.ndarray) -> pd.Series:
        pass
