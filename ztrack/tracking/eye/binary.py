import cv2
import numpy as np

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
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

    def _track_contours(self, img: np.ndarray):
        contours = self._binary_segmentation(img, self.params.threshold)

        # get the 3 largest contours
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
        assert len(contours) == 3

        centers = np.array(
            [zcv.contour_center(contour) for contour in contours]
        )
        left_eye, right_eye, swim_bladder = self._sort_centers(centers)

        return contours[left_eye], contours[right_eye], contours[swim_bladder]
