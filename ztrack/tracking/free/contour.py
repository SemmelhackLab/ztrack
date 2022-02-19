import cv2
import numpy as np
from skimage.graph import route_through_array
from skimage.morphology import skeletonize

import ztrack.utils.cv as zcv
from ztrack.tracking.params import Params
from ztrack.utils.variable import Float, Int, UInt8

from .base import BaseFreeSwimTracker


class ContourFreeSwimTracker(BaseFreeSwimTracker):
    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma_eye = Float("Eye sigma (px)", 0, 0, 100, 0.1)
            self.sigma_tail = Float("Tail sigma (px)", 0, 0, 100, 0.1)
            self.block_size = Int("Block size", 99, 3, 200)
            self.c = Int("C", -5, -100, 100)
            self.threshold_segmentation = UInt8("Segmentation threshold", 70)
            self.threshold_left_eye = UInt8("Left eye threshold", 70)
            self.threshold_right_eye = UInt8("Right eye threshold", 70)
            self.threshold_swim_bladder = UInt8("Swim bladder threshold", 70)
            self.n_points = Int("Number of points", 51, 2, 100)

    def __init__(self, roi=None, params: dict = None, *, verbose=0, debug=False):
        super().__init__(roi, params, verbose=verbose, debug=debug)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "contour"

    @staticmethod
    def display_name():
        return "Contour skeletonization"

    @staticmethod
    def _find_ends(img, px, py):
        yx = np.column_stack(np.where(img))
        dist = np.linalg.norm(yx - (py, px), axis=1)
        return yx[dist.argmin()], yx[dist.argmax()]

    def _find_path(self, img, point):
        p1, p2 = self._find_ends(img, *point)
        path, _ = route_through_array(1 - img, p1, p2, fully_connected=True)
        return np.array(path)[:, ::-1]

    def _track_tail(self, src, point, angle):
        p = self.params
        img = zcv.gaussian_blur(src, p.sigma_tail)
        img_thresh = zcv.adaptive_threshold(img, p.block_size, p.c)
        contours = zcv.find_contours(img_thresh)
        fish_contour = max(contours, key=cv2.contourArea)
        fish_mask = np.zeros_like(src)
        cv2.drawContours(fish_mask, [fish_contour], -1, 255, cv2.FILLED)
        img_ske = skeletonize(fish_mask != 0)
        tail = self._find_path(img_ske, point)

        return zcv.interpolate_tail(tail, self.params.n_points)
