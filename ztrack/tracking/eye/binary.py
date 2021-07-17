import cv2
import numpy as np
import pandas as pd

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.tracking.variable import Float, UInt8


class BinaryEyeTracker(EyeTracker):
    class Params(EyeParams):
        def __init__(self):
            super().__init__()
            self.sigma = Float("Sigma", 0, 0, 100, 0.1)
            self.threshold = UInt8("Threshold", 127)

    def __init__(self):
        super().__init__()
        self._params = self.Params()

    @property
    def params(self):
        return self._params

    @property
    def name(self):
        return "binary"

    @property
    def display_name(self):
        return "Binary threshold"

    def _track_region(self, img) -> pd.Series:
        pass

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
