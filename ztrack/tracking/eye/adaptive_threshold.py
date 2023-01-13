from typing import Optional

import cv2
import numpy as np
from skimage.morphology import remove_small_objects

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.shape import Rectangle
from ztrack.utils.variable import Angle, Bool, Float, Int, Point, Rect, UInt8


class AdaptiveThresholdEyeTracker(EyeTracker):
    def __init__(self, roi=None, params: Optional[dict] = None, *, verbose=0, debug=False):
        super().__init__(roi, params, verbose=verbose, debug=debug)

        self._left_eye_bbox = Rectangle(0, 0, 1, 1, 4, "b")
        self._right_eye_bbox = Rectangle(0, 0, 1, 1, 4, "r")
        self._bboxes = [
            self._left_eye_bbox,
            self._right_eye_bbox,
        ]

    class __Params(EyeParams):
        def __init__(self, params: Optional[dict] = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)

            self.bbox_l = Rect("Left eye", (0, 0, 30, 30))
            self.block_size_l = Int("Block size (px)", 11, 1, 299, odd_only=True)
            self.c_l = Int("C", 0, -100, 100)

            self.bbox_r = Rect("Right eye", (0, 0, 30, 30))
            self.block_size_r = Int("Block size (px)", 11, 1, 299, odd_only=True)
            self.c_r = Int("C", 0, -100, 100)

            self.swim_bladder_center = Point("Swim bladder center", (0, 0))
            self.swim_bladder_length = UInt8("Swim bladder length", 20)
            self.swim_bladder_width = UInt8("Swim bladder width", 30)
            self.swim_bladder_orientation = Angle("Swim bladder orientation", 270)

            self.min_size = Int("Minimum size (px)", 5, 0, 200)

            self.invert = Bool("invert", True)

    @property
    def shapes(self):
        return super().shapes + self._bboxes

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "adaptive"

    @staticmethod
    def display_name():
        return "Adaptive threshold"

    def annotate(self, frame: np.ndarray) -> None:
        super().annotate(frame)

        p = self.params

        for i, j in zip(
            self._bboxes,
            (
                p.bbox_l,
                p.bbox_r,
            ),
        ):
            i.visible = True
            x, y, w, h = j
            x -= self.roi.value[0]
            y -= self.roi.value[1]
            i.x, i.y, i.w, i.h = x, y, w, h

    def _track_contours(self, img: np.ndarray):
        p = self.params

        contours = []

        temp = np.zeros_like(img)

        for part in ("l", "r"):
            x, y, w, h = getattr(p, f"bbox_{part}")
            x -= self.roi.value[0]
            y -= self.roi.value[1]

            im = img[y : y + h, x : x + w]

            block_size = getattr(p, f"block_size_{part}")
            c = getattr(p, f"c_{part}")
            threshold = zcv.adaptive_threshold(im, block_size, c)
            threshold = (remove_small_objects(threshold > 0, p.min_size) * 255).astype(np.uint8)

            temp[y : y + h, x : x + w] = threshold

            points = np.concatenate(zcv.find_contours(threshold))
            contour = cv2.convexHull(points) + np.array([[x, y]])

            contours.append(contour)

        if self._debug:
            cv2.imshow("debug", temp)

        return contours

    def _fit_ellipses(self, contours):
        ellipses = np.array([zcv.fit_ellipse_moments(contour) for contour in contours])
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
