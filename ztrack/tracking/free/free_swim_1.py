import cv2
import numpy as np

import ztrack.utils.cv as zcv
from ztrack.tracking.eye.eye_tracker import EyeTracker
from ztrack.tracking.params import Params
from ztrack.utils.exception import TrackingError
from ztrack.utils.variable import Angle, Float, Int, UInt8

from .base import BaseFreeSwimTracker


class FreeSwim1(BaseFreeSwimTracker):
    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma_eye = Float("Eye sigma (px)", 0, 0, 100, 0.1)
            self.sigma_tail = Float("Tail sigma (px)", 2.5, 0, 100, 0.1)
            self.threshold_segmentation = UInt8("Segmentation threshold", 27)
            self.threshold_eye = UInt8("Eye threshold", 124)
            self.n_steps = Int("Number of steps", 20, 3, 20)
            self.tail_length = Int("Tail length (px)", 95, 0, 1000)
            self.search_angle = Angle("Search angle (°)", 60)

            self.swim_bladder_distance = Int("Swim bladder distance", 29, 0, 200)
            self.swim_bladder_length = UInt8("Swim bladder length", 7)
            self.swim_bladder_width = UInt8("Swim bladder width", 4)

            # self.r = Int("Arena radius", 365, 0, 1000)
            # self.cx = Int("Arena center x", 365, 0, 1000)
            # self.cy = Int("Arena center y", 365, 0, 1000)

    @property
    def _Params(self):
        return self.__Params

    @staticmethod
    def name():
        return "free_swim_1"

    @staticmethod
    def display_name():
        return "Free swim 1"

    def _track_tail(self, src, point, angle):
        p = self.params
        search_angle = np.deg2rad(p.search_angle / 2)
        img = zcv.gaussian_blur(src, p.sigma_tail)
        tail = zcv.sequential_track_tail(
            img, point, angle, search_angle, p.n_steps, p.tail_length, ""
        )

        return tail

    def _track_eyes(self, src):
        p = self.params
        contours = zcv.binary_segmentation(src, self.params.threshold_segmentation)
        fish_contour = max(contours, key=cv2.contourArea)
        mask = cv2.drawContours(np.zeros_like(src), [fish_contour], -1, 1, -1)
        img = mask * src
        # eye_candidates = zcv.binary_segmentation(img, self.params.threshold_eye)
        thresholded = zcv.binary_threshold(img, p.threshold_eye)
        eye_candidates = zcv.find_contours(thresholded)

        if self._debug:
            cv2.imshow(
                "img",
                np.concatenate(
                    (
                        zcv.binary_threshold(src, p.threshold_segmentation),
                        zcv.binary_threshold(img, p.threshold_eye),
                    ),
                    axis=1,
                ),
            )

        if len(eye_candidates) >= 2:
            eye_contours = sorted(eye_candidates, key=cv2.contourArea, reverse=True)[:2]
        # elif len(eye_candidates) == 1:
        #     x0, x1 = np.where(np.diff(np.pad(thresholded.max(0), 1)))[0]
        #     y0, y1 = np.where(np.diff(np.pad(thresholded.max(1), 1)))[0]
        #     b = thresholded[y0:y1, x0:x1]

        #     erode = b.copy()
        #     while True:
        #         erode = cv2.erode(erode, np.ones((3, 3)))
        #         ret, markers = cv2.connectedComponents(erode)
        #         if erode.sum() == 0:
        #             raise TrackingError("No eye detected")
        #         if ret == 3:
        #             markers[b == 0] = 0
        #             break

        #     watershed = cv2.watershed(cv2.cvtColor(img[y0:y1, x0:x1], cv2.COLOR_GRAY2RGB), markers)
        #     watershed[b == 0] = 0
        #     # cv2.imshow("watershed", (watershed * 127).astype(np.uint8))
        #     eye_contours = [zcv.find_contours((watershed == i).astype(np.uint8))[0] + (x0, y0) for i in (1, 2)]
        else:
            raise TrackingError("No eye detected")

        eye_centers = np.array([zcv.contour_center(contour) for contour in eye_contours])
        fish_center = zcv.contour_center(fish_contour)

        eye_contours = (
            eye_contours if np.cross(*eye_centers - fish_center) > 0 else eye_contours[::-1]
        )

        eyes = np.array([zcv.fit_ellipse_moments(contour) for contour in eye_contours])

        eye_centers = eyes[:, :2]
        midpoint = eye_centers.mean(0)
        u = eye_centers[1] - eye_centers[0]
        u = u / np.linalg.norm(u)
        v = np.array([-u[1], u[0]])
        swim_bladder_center = midpoint + p.swim_bladder_distance * v

        swim_bladder = (
            *swim_bladder_center,
            p.swim_bladder_length,
            p.swim_bladder_width,
            np.angle(v[0] + v[1] * 1j, deg=True),
        )

        ellipses = np.concatenate((eyes, (swim_bladder,)))

        ellipses = EyeTracker._correct_orientation(ellipses)
        return ellipses

    def _track_img(self, img: np.ndarray):
        p = self.params

        # img[self.get_outside_mask(img)] = 0
        ellipses = self._track_eyes(img)

        centers = ellipses[:, :2]
        sb_center = centers[2]
        midpoint = centers[:2].mean(0)
        midline = sb_center - midpoint
        opp_heading = np.arctan2(*midline[::-1])
        sb_search_angle = np.deg2rad(ellipses[2, -1])
        sb_posterior = np.round(
            sb_center
            - ellipses[2, 2] * np.array([np.cos(sb_search_angle), np.sin(sb_search_angle)])
        ).astype(int)

        try:
            tail = self._track_tail(img, sb_posterior, opp_heading)
        except TrackingError:
            tail = None

        return np.concatenate((ellipses.ravel(), tail.ravel()))
