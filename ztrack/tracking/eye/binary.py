import cv2
import numpy as np
import pandas as pd

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.variable import Float, UInt8


class BinaryEyeTracker(EyeTracker):
    def __init__(self, params: dict = None):
        super().__init__(params)

    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma", 0, 0, 100, 0.1)
            self.threshold = UInt8("Threshold", 127)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "binary"

    @staticmethod
    def display_name():
        return "Binary threshold"

    def _track_ellipses(self, src: np.ndarray):
        img = self._preprocess(src, self.params.sigma)

        contours = self._binary_segmentation(img, self.params.threshold)

        # get the 3 largest contours
        largest3 = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
        assert len(largest3) == 3

        # fit ellipses (x, y, semi-major axis, semi-minor axis, theta in
        # degrees)
        ellipses = self._fit_ellipses(largest3)

        centers = ellipses[:, :2]
        ellipses = ellipses[list(self._sort_centers(centers))]

        return self._correct_orientation(ellipses)

    def _track_frame(self, frame: np.ndarray) -> pd.Series:
        pass
