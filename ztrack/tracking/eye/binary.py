import cv2
import numpy as np

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.exception import TrackingError
from ztrack.utils.variable import Float, UInt8


class BinaryEyeTracker(EyeTracker):
    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)

    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
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

    def _track_img(self, img: np.ndarray) -> np.ndarray:
        img = self._preprocess(img, self.params.sigma)
        return self._track_ellipses(img)

    def _track_ellipses(self, src: np.ndarray):
        try:
            contours = self._binary_segmentation(src, self.params.threshold)

            # get the 3 largest contours
            largest3 = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
            assert len(largest3) == 3

            # fit ellipses (x, y, semi-major axis, semi-minor axis, theta in
            # degrees)
            ellipses = self._fit_ellipses(largest3)

            centers = ellipses[:, :2]
            ellipses = ellipses[list(self._sort_centers(centers))]

            return self._correct_orientation(ellipses)
        except (cv2.error, AssertionError):
            raise TrackingError
