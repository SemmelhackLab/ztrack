import cv2
import numpy as np

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.variable import Float, Int


class AdaptiveThresholdEyeTracker(EyeTracker):
    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)

    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
            self.block_size = Int("Block size (px)", 11, 1, 99, odd_only=True)
            self.c = Int("C", 0, -100, 100)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "adaptive"

    @staticmethod
    def display_name():
        return "Adaptive threshold"

    def _track_contours(self, img: np.ndarray):
        p = self.params
        threshold = zcv.adaptive_threshold(img, p.block_size, p.c)
        cv2.imshow("thresh", threshold)
        contours = zcv.find_contours(threshold)

        # get the 3 largest contours
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
        assert len(contours) == 3

        centers = np.array(
            [zcv.contour_center(contour) for contour in contours]
        )
        left_eye, right_eye, swim_bladder = self._sort_centers(centers)

        return contours[left_eye], contours[right_eye], contours[swim_bladder]
