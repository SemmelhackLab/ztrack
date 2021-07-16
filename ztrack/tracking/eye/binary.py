import cv2
import numpy as np
import pandas as pd

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.geometry import wrap_degrees
from ztrack.tracking.variable import Float, UInt8


class BinaryEyeTracker(EyeTracker):
    class Params(EyeParams):
        def __init__(self):
            super().__init__()
            self.sigma = Float("Sigma", 0, 0, 100, .1)
            self.threshold = UInt8("Threshold", 127)

    def __init__(self):
        super().__init__()
        self._params = BinaryEyeTracker.Params()

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
        img = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)

        # invert image if mean intensity is greater than 127
        if cv2.mean(img)[0] > 127:
            img = cv2.bitwise_not(img)

        if self.params.sigma > 0:
            img = cv2.GaussianBlur(img, (0, 0), self.params.sigma)

        # binary threshold
        img = cv2.threshold(
            img, self.params.threshold, 255, cv2.THRESH_BINARY
        )[1]

        # find contours
        contours = cv2.findContours(
            img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )[0]

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

        # correct orientation
        midpoint = centers[eyes].mean(0)
        midline = midpoint - centers[swim_bladder]
        heading = np.rad2deg(np.arctan2(*midline[::-1]))
        is_opposite = abs(wrap_degrees(heading - ellipses[:, -1])) > 90
        ellipses[is_opposite, -1] = wrap_degrees(
            ellipses[is_opposite, -1] - 180
        )

        return ellipses[[left_eye, right_eye, swim_bladder]]
