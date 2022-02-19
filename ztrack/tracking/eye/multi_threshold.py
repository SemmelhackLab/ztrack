import cv2
import numpy as np

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.exception import TrackingError
from ztrack.utils.variable import Float, UInt8


class MultiThresholdEyeTracker(EyeTracker):
    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
            self.threshold_segmentation = UInt8("Segmentation threshold", 127)
            self.threshold_left_eye = UInt8("Left eye threshold", 127)
            self.threshold_right_eye = UInt8("Right eye threshold", 127)
            self.threshold_swim_bladder = UInt8("Swim bladder threshold", 127)

    def __init__(self, roi=None, params: dict = None, *, verbose=0, debug=False):
        super().__init__(roi, params, verbose=verbose, debug=debug)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "multithreshold"

    @staticmethod
    def display_name():
        return "Multi-threshold"

    def _track_contours(self, img: np.ndarray):
        p = self.params

        # segment the image with binary threshold
        contours = self._binary_segmentation(img, p.threshold_segmentation)

        # get the 3 largest contours
        if len(contours) < 3:
            raise TrackingError("Less than 3 contours detected")

        largest3 = sorted(contours, key=cv2.contourArea, reverse=True)[:3]

        # calculate the contour centers
        centers = np.array([zcv.contour_center(c) for c in largest3])

        # sort contours (0: left eye, 1: right eye, 2: swim bladder)
        centers = centers[list(self._sort_centers(centers))]

        # apply binary threshold for each body part and get the contour closest to its center
        thresholds = [
            p.threshold_left_eye,
            p.threshold_right_eye,
            p.threshold_swim_bladder,
        ]

        results = []
        for i, (threshold, center) in enumerate(zip(thresholds, centers)):
            # segment the image with binary threshold of the body part
            contours = self._binary_segmentation(img, threshold)
            # get the contour closest to the body part's center
            results.append(zcv.nearest_contour(contours, tuple(center)))

        return results
