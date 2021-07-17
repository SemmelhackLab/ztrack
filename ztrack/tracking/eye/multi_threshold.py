import cv2
import numpy as np
import pandas as pd

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.tracking.variable import ROI, Float, UInt8
from ztrack.utils.cv import binary_threshold, find_contours, is_in_contour
from ztrack.utils.geometry import wrap_degrees


class MultiThresholdEyeTracker(EyeTracker):
    class Params(EyeParams):
        def __init__(self):
            super().__init__()
            self.roi = ROI("ROI", None)
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

    def _track_region(self, img) -> pd.Series:
        pass

    def _track_ellipses(self, src: np.ndarray):
        img = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)

        # invert image if mean intensity is greater than 127
        if cv2.mean(img)[0] > 127:
            img = cv2.bitwise_not(img)

        contours_left_eye = find_contours(
            binary_threshold(img, self.params.threshold_left_eye)
        )
        contours_right_eye = find_contours(
            binary_threshold(img, self.params.threshold_right_eye)
        )
        contours_swim_bladder = find_contours(
            binary_threshold(img, self.params.threshold_swim_bladder)
        )

        # binary threshold
        img = binary_threshold(img, self.params.threshold_segmentation)

        # find contours
        contours = find_contours(img)

        # get the 3 largest contours
        largest3 = sorted(contours, key=cv2.contourArea, reverse=True)[:3]

        assert len(largest3) == 3

        # fit ellipses (x, y, semi-major axis, semi-minor axis, theta in degrees)
        ellipses = np.array(
            [
                (x, y, b / 2, a / 2, theta - 90)
                for (x, y), (a, b), theta in map(
                    cv2.fitEllipse, map(cv2.convexHull, largest3)
                )
            ]
        )

        # identify contours
        centers = ellipses[:, :2]
        idx = np.arange(3)
        swim_bladder = np.argmin(
            [np.linalg.norm(np.subtract(*centers[idx != i])) for i in idx]
        )
        eyes = idx[idx != swim_bladder]
        left_eye, right_eye = (
            eyes
            if np.cross(*centers[eyes] - centers[swim_bladder]) > 0
            else eyes[::-1]
        )

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

        ellipses = np.array(
            [
                (x, y, b / 2, a / 2, theta - 90)
                for (x, y), (a, b), theta in map(
                    cv2.fitEllipse, map(cv2.convexHull, largest3)
                )
            ]
        )

        # correct orientation
        midpoint = centers[eyes].mean(0)
        midline = midpoint - centers[swim_bladder]
        heading = np.rad2deg(np.arctan2(*midline[::-1]))
        is_opposite = abs(wrap_degrees(heading - ellipses[:, -1])) > 90
        ellipses[is_opposite, -1] = wrap_degrees(
            ellipses[is_opposite, -1] - 180
        )

        return ellipses[[left_eye, right_eye, swim_bladder]]
