import cv2
import numpy as np
from skimage.util import img_as_ubyte

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.cv import winsorize
from ztrack.utils.exception import TrackingError
from ztrack.utils.variable import Angle, Float, Int, Point, UInt8


class EyesOnlyTracker(EyeTracker):
    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)
            self.qmin = Float("qmin", 0.05, 0, 1, 0.01)
            self.qmax = Float("qmax", 0.99, 0, 1, 0.01)
            self.threshold_segmentation = UInt8("Segmentation threshold", 127)
            self.threshold_left_eye = UInt8("Left eye threshold", 127)
            self.threshold_right_eye = UInt8("Right eye threshold", 127)
            self.swim_bladder_center = Point("Swim bladder center", (0, 0))
            self.swim_bladder_length = UInt8("Swim bladder length", 20)
            self.swim_bladder_width = UInt8("Swim bladder width", 30)
            self.swim_bladder_orientation = Angle(
                "Swim bladder orientation", 270
            )
            self.invert = Int("invert", 0, -1, 1)

    def __init__(
        self, roi=None, params: dict = None, *, verbose=0, debug=False
    ):
        super().__init__(roi, params, verbose=verbose, debug=debug)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "eyes_only"

    @staticmethod
    def display_name():
        return "Eyes only"

    @staticmethod
    def _sort_centers(centers):
        return centers[:, 0].argsort()

    def _track_contours(self, img: np.ndarray):
        p = self.params

        img = img_as_ubyte(winsorize(img, p.qmin, p.qmax))

        if self._debug:
            cv2.imshow(img)

        # segment the image with binary threshold
        contours = self._binary_segmentation(img, p.threshold_segmentation)

        # get the 3 largest contours
        if len(contours) < 2:
            raise TrackingError("Less than 2 contours detected")

        largest2 = sorted(contours, key=cv2.contourArea, reverse=True)[:2]

        # calculate the contour centers
        centers = np.array([zcv.contour_center(c) for c in largest2])

        # sort contours (0: left eye, 1: right eye)
        centers = centers[self._sort_centers(centers)]

        # apply binary threshold for each body part and get the contour closest to its center
        thresholds = [
            p.threshold_left_eye,
            p.threshold_right_eye,
        ]

        results = []
        for i, (threshold, center) in enumerate(zip(thresholds, centers)):
            # segment the image with binary threshold of the body part
            contours = self._binary_segmentation(img, threshold)
            # get the contour closest to the body part's center
            results.append(zcv.nearest_contour(contours, tuple(center)))

        return results

    def _fit_ellipses(self, contours):
        ellipses = np.array(
            [zcv.fit_ellipse_moments(contour) for contour in contours]
        )
        return ellipses

    def _track_img(self, img: np.ndarray) -> np.ndarray:
        eyes = super()._track_img(img)
        p = self.params
        x = p.swim_bladder_center[0] - self.roi.value[0]
        y = p.swim_bladder_center[1] - self.roi.value[1]
        swim_bladder = (
            x,
            y,
            p.swim_bladder_length,
            p.swim_bladder_width,
            p.swim_bladder_orientation,
        )
        return self._correct_orientation(np.row_stack((eyes, swim_bladder)))
