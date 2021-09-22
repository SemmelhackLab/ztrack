from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from decord import VideoReader
from scipy.interpolate import splev, splprep
from skimage.draw import circle_perimeter
from tqdm import tqdm

from ztrack.tracking.eye.eye_tracker import EyeTracker
from ztrack.tracking.params import Params
from ztrack.utils.cv import find_contours, is_in_contour
from ztrack.utils.exception import TrackingError
from ztrack.utils.geometry import angle_diff, wrap_degrees
from ztrack.utils.math import split_int
from ztrack.utils.shape import Points
from ztrack.utils.variable import Angle, Float, Int, UInt8


class FreeSwimTracker(EyeTracker):
    class __Params(Params):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma_eye = Float("Eye sigma (px)", 0, 0, 100, 0.1)
            self.sigma_tail = Float("Tail sigma (px)", 0, 0, 100, 0.1)
            self.block_size = Int("Block size", 99, 3, 200)
            self.c = Int("C", -5, -100, 100)
            self.threshold_segmentation = UInt8("Segmentation threshold", 200)
            self.threshold_left_eye = Int("Left eye threshold", 0, -128, 127)
            self.threshold_right_eye = Int("Right eye threshold", 0, -128, 127)
            self.threshold_swim_bladder = Int(
                "Swim bladder threshold", 0, -128, 127
            )
            self.n_steps = Int("Number of steps", 20, 3, 20)
            self.n_points = Int("Number of points", 51, 2, 100)
            self.length = Int("Tail length (px)", 90, 0, 1000)
            self.theta = Angle("Search angle (°)", 60)

    @property
    def _Params(self):
        return self.__Params

    @property
    def shapes(self):
        return [
            self._left_eye,
            self._right_eye,
            self._swim_bladder,
            self._points,
        ]

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)
        self._bg = None
        self._is_bg_bright = None
        self._video_path = None
        self._points = Points(np.array([[0, 0]]), 1, "m", symbol="+")
        cv2.namedWindow("Test")

    @staticmethod
    def name():
        return "freeswim"

    @staticmethod
    def display_name():
        return "Free swim"

    def calculate_background(self, video_path):
        if self._verbose:
            print("Calculating background...")
        sub = cv2.createBackgroundSubtractorMOG2()
        vr = VideoReader(video_path)
        if self._verbose:
            vr = tqdm(vr)
        for frame in vr:
            sub.apply(cv2.cvtColor(frame.asnumpy(), cv2.COLOR_RGB2GRAY))

        bg = sub.getBackgroundImage()
        cv2.imwrite(str(Path(video_path).with_suffix(".png")), bg)
        is_bg_bright = cv2.mean(bg)[0] > 127

        return is_bg_bright, bg

    def set_video(self, video_path):
        self._bg = None
        self._video_path = video_path

        if video_path is not None:
            bg_path = Path(video_path).with_suffix(".png")
            if bg_path.exists():
                self._bg = cv2.imread(str(bg_path), 0)
                self._is_bg_bright = cv2.mean(self._bg)[0] > 127

    def _track_img(self, img: np.ndarray):
        if self._bg is None:
            self._is_bg_bright, self._bg = self.calculate_background(
                self._video_path
            )

        img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        bg = self._bg[self.roi.to_slice()]

        if self._is_bg_bright:
            img = cv2.subtract(bg, img)
        else:
            img = cv2.subtract(img, bg)

        ellipses = self._track_ellipses(img)

        centers = ellipses[:, :2]
        sb_center = centers[2]
        midpoint = centers[:2].mean(0)
        midline = sb_center - midpoint
        opp_heading = np.arctan2(*midline[::-1])
        sb_theta = np.deg2rad(ellipses[2, -1])
        sb_posterior = np.round(
            sb_center
            - ellipses[2, 2] * np.array([np.cos(sb_theta), np.sin(sb_theta)])
        ).astype(int)

        try:
            tail = self._track_tail(img, sb_posterior, opp_heading)
        except TrackingError:
            tail = None

        return ellipses, tail

    @classmethod
    def _results_to_series(cls, results):
        eye, tail = results
        eyes_midpoint = eye[:2, :2].mean(0)
        swim_bladder_center = eye[-1, :2]
        midline = eyes_midpoint - swim_bladder_center
        x2, x1 = midline
        heading = np.rad2deg(np.arctan2(x1, x2))
        theta_l, theta_r = eye[:2, -1]
        angle_l = wrap_degrees(theta_l - heading)
        angle_r = wrap_degrees(heading - theta_r)
        s = pd.Series(eye.ravel(), index=cls._index)
        s["left_eye", "angle"] = angle_l
        s["right_eye", "angle"] = angle_r
        s["heading"] = heading

        if tail is not None:
            n_points = len(tail)
            idx = pd.MultiIndex.from_product(
                ((f"point{i:02d}" for i in range(n_points)), ("x", "y"))
            )
            s = pd.concat([s, pd.Series(tail.ravel(), idx)])

        return s

    def annotate_from_series(self, series: pd.Series) -> None:
        ellipse_shapes = [self._left_eye, self._right_eye, self._swim_bladder]
        body_parts = ["left_eye", "right_eye", "swim_bladder"]
        for i, j in zip(ellipse_shapes, body_parts):
            i.visible = True
            s = series[j]
            i.cx, i.cy, i.a, i.b, i.theta = s.cx, s.cy, s.a, s.b, s.theta

        if "point00" in series:
            idx = [f"point{i:02d}" for i in range(self.params.n_points)]
            tail = series.loc[idx].values.reshape(-1, 2)
            self._points.visible = True
            self._points.data = tail
        else:
            self._points.visible = False

    def _track_tail(self, src, point, angle):
        theta = np.deg2rad(self.params.theta / 2)

        if self.params.sigma_eye > 0:
            img = cv2.GaussianBlur(src, (0, 0), self.params.sigma_eye)
        else:
            img = src

        h, w = img.shape
        tail = np.zeros((self.params.n_steps + 1, 2), dtype=int)
        tail[0] = point
        step_lengths = split_int(
            round(self.params.length), self.params.n_steps
        )
        for i in range(self.params.n_steps):
            points = np.column_stack(
                circle_perimeter(*point, step_lengths[i], shape=(w, h))
            )
            angles = np.arctan2(*reversed((points - point).T))
            idx = angle_diff(angles, angle) < theta
            points, angles = points[idx], angles[idx]
            x, y = points.T

            try:
                argmax = img[y, x].argmax()
            except ValueError:
                raise TrackingError

            angle = angles[argmax]
            tail[i + 1] = point = points[argmax]

        return self._interpolate_tail(tail, self.params.n_points)

    @staticmethod
    def _interpolate_tail(tail: np.ndarray, n_points: int) -> np.ndarray:
        tck = splprep(tail.T)[0]
        return np.column_stack(splev(np.linspace(0, 1, n_points), tck))

    def _track_ellipses(self, src: np.ndarray):
        try:
            if self.params.sigma_eye > 0:
                img = cv2.GaussianBlur(src, (0, 0), self.params.sigma_eye)
            else:
                img = src.copy()

            block_size = self.params.block_size

            if block_size % 2 == 0:
                block_size += 1

            img_thresh = cv2.adaptiveThreshold(
                img,
                255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                block_size,
                self.params.c,
            )

            contours = find_contours(img_thresh)
            fish_contour = max(contours, key=cv2.contourArea)
            fish_mask = np.zeros_like(src)
            cv2.drawContours(fish_mask, [fish_contour], -1, 255, cv2.FILLED)

            img[fish_mask == 0] = 0
            img = cv2.equalizeHist(img)

            t = self.params.threshold_segmentation

            contours_left_eye = self._binary_segmentation(
                img, t + self.params.threshold_left_eye
            )
            contours_right_eye = self._binary_segmentation(
                img, t + self.params.threshold_right_eye
            )
            contours_swim_bladder = self._binary_segmentation(
                img, t + self.params.threshold_swim_bladder
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
