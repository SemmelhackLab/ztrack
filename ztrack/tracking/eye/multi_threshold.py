import cv2
import numpy as np
import pandas as pd

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.variable import Float, UInt8
from ztrack.utils.cv import is_in_contour


class MultiThresholdEyeTracker(EyeTracker):
    class Params(EyeParams):
        def __init__(self):
            super().__init__()
            self.sigma = Float("Sigma", 0, 0, 100, 0.1)
            self.threshold_segmentation = UInt8("Segmentation threshold", 127)
            self.threshold_left_eye = UInt8("Left eye threshold", 127)
            self.threshold_right_eye = UInt8("Right eye threshold", 127)
            self.threshold_swim_bladder = UInt8("Swim bladder threshold", 127)

    def __init__(self):
        super().__init__()
        self._params = self.Params()

    @property
    def params(self):
        return self._params

    @property
    def name(self):
        return "multithreshold"

    @property
    def display_name(self):
        return "Multi-threshold"

    def _track_ellipses(self, src: np.ndarray):
        img = self._preprocess(src)

        contours_left_eye = self._binary_segmentation(
            img, self.params.threshold_left_eye
        )
        contours_right_eye = self._binary_segmentation(
            img, self.params.threshold_right_eye
        )
        contours_swim_bladder = self._binary_segmentation(
            img, self.params.threshold_swim_bladder
        )
        contours = self._binary_segmentation(
            img, self.params.threshold_segmentation
        )

        # get the 3 largest contours
        largest3 = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
        assert len(largest3) == 3

        ellipses = self._fit_ellipses(largest3)

        # identify contours
        centers = ellipses[:, :2]
        left_eye, right_eye, swim_bladder = self._sort_centers(centers)

        largest3[swim_bladder] = max(
            contours_swim_bladder,
            key=lambda cnt: is_in_contour(cnt, tuple(centers[swim_bladder])),
        )
        largest3[left_eye] = max(
            contours_left_eye,
            key=lambda cnt: is_in_contour(cnt, tuple(centers[left_eye])),
        )
        largest3[right_eye] = max(
            contours_right_eye,
            key=lambda cnt: is_in_contour(cnt, tuple(centers[right_eye])),
        )

        ellipses = self._fit_ellipses(largest3)
        ellipses = ellipses[[left_eye, right_eye, swim_bladder]]

        return self._correct_orientation(ellipses)

    def _track_frame(self, frame: np.ndarray) -> pd.Series:
        pass
