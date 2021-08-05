import cv2
import numpy as np

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.cv import is_in_contour
from ztrack.utils.exception import TrackingError
from ztrack.utils.variable import Float, UInt8


class MultiThresholdEyeTracker(EyeTracker):
    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 0, 0, 100, 0.1)
            self.threshold_segmentation = UInt8("Segmentation threshold", 127)
            self.threshold_left_eye = UInt8("Left eye threshold", 127)
            self.threshold_right_eye = UInt8("Right eye threshold", 127)
            self.threshold_swim_bladder = UInt8("Swim bladder threshold", 127)

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "multithreshold"

    @staticmethod
    def display_name():
        return "Multi-threshold"

    def _track_ellipses(self, src: np.ndarray):
        try:
            img = self._preprocess(src, self.params.sigma)

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
                key=lambda cnt: is_in_contour(
                    cnt, tuple(centers[swim_bladder])
                ),
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
        except (cv2.error, AssertionError):
            raise TrackingError
