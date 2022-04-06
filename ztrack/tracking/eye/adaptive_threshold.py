import cv2
import numpy as np
from skimage.morphology import remove_small_objects

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.shape import Rectangle
from ztrack.utils.variable import Float, Int, Rect


class AdaptiveThresholdEyeTracker(EyeTracker):
    def __init__(
        self, roi=None, params: dict = None, *, verbose=0, debug=False
    ):
        super().__init__(roi, params, verbose=verbose, debug=debug)

        self._left_eye_bbox = Rectangle(0, 0, 1, 1, 4, "b")
        self._right_eye_bbox = Rectangle(0, 0, 1, 1, 4, "r")
        self._swim_bladder_bbox = Rectangle(0, 0, 1, 1, 4, "g")
        self._bboxes = [
            self._left_eye_bbox,
            self._right_eye_bbox,
            self._swim_bladder_bbox,
        ]

    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 2, 0, 100, 0.1)

            self.bbox_l = Rect("Left eye", (0, 0, 30, 30))
            self.block_size_l = Int(
                "Block size (px)", 11, 1, 99, odd_only=True
            )
            self.c_l = Int("C", 0, -100, 100)

            self.bbox_r = Rect("Right eye", (0, 0, 30, 30))
            self.block_size_r = Int(
                "Block size (px)", 11, 1, 99, odd_only=True
            )
            self.c_r = Int("C", 0, -100, 100)

            self.bbox_sb = Rect("Swim bladder", (0, 0, 30, 30))
            self.block_size_sb = Int(
                "Block size (px)", 11, 1, 99, odd_only=True
            )
            self.c_sb = Int("C", 0, -100, 100)

            self.min_size = Int("Minimum size (px)", 5, 0, 200)

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

        for i, j in zip(self._bboxes, (p.bbox_l, p.bbox_r, p.bbox_sb)):
            i.visible = True
            x, y, w, h = j
            x -= self.roi.value[0]
            y -= self.roi.value[1]
            i.x, i.y, i.w, i.h = x, y, w, h

    def _track_contours(self, img: np.ndarray):
        p = self.params

        contours = []

        temp = np.zeros_like(img)

        for part in ("l", "r", "sb"):
            x, y, w, h = getattr(p, f"bbox_{part}")
            x -= self.roi.value[0]
            y -= self.roi.value[1]

            im = img[y : y + h, x : x + w]

            block_size = getattr(p, f"block_size_{part}")
            c = getattr(p, f"c_{part}")
            threshold = zcv.adaptive_threshold(im, block_size, c)
            threshold = (
                remove_small_objects(threshold > 0, p.min_size) * 255
            ).astype(np.uint8)

            temp[y : y + h, x : x + w] = threshold

            points = np.concatenate(zcv.find_contours(threshold))
            contour = cv2.convexHull(points) + np.array([[x, y]])

            # temp = np.zeros_like(im)
            # ret = cv2.drawContours(temp, [contour], -1, 255, -1)
            # cv2.imshow(part, ret)

            contours.append(contour)

        if self._debug:
            cv2.imshow("debug", temp)

        return contours
