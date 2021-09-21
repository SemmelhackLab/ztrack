from pathlib import Path

import cv2
import numpy as np
from decord import VideoReader
from tqdm import tqdm

from ztrack.tracking.eye.eye_tracker import EyeParams, EyeTracker
from ztrack.utils.cv import is_in_contour
from ztrack.utils.exception import TrackingError
from ztrack.utils.variable import Float, UInt8


class FreeSwimTracker(EyeTracker):
    class __Params(EyeParams):
        def __init__(self, params: dict = None):
            super().__init__(params)
            self.sigma = Float("Sigma (px)", 0, 0, 100, 0.1)
            self.threshold_segmentation = UInt8("Segmentation threshold", 127)
            self.threshold_left_eye = UInt8("Left eye threshold", 127)
            self.threshold_right_eye = UInt8("Right eye threshold", 127)
            self.threshold_swim_bladder = UInt8("Swim bladder threshold", 127)

    @property
    def _Params(self):
        return self.__Params

    def __init__(self, roi=None, params: dict = None, *, verbose=0):
        super().__init__(roi, params, verbose=verbose)
        self._bg = None
        self._is_bg_bright = None
        self._video_path = None
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
            sub.apply(frame.asnumpy(), 0)

        bg = sub.getBackgroundImage()
        cv2.imwrite(str(Path(video_path).with_suffix(".png")), bg)
        is_bg_bright = cv2.mean(bg)[0] > 127

        return is_bg_bright, bg

    def set_video(self, video_path):
        self._bg = None
        bg_path = Path(video_path).with_suffix(".png")
        if bg_path.exists():
            self._bg = cv2.imread(str(bg_path), 0)
            self._is_bg_bright = cv2.mean(self._bg)[0] > 127

        self._video_path = video_path

    def _track_img(self, img: np.ndarray) -> np.ndarray:
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

        if self.params.sigma > 0:
            img = cv2.GaussianBlur(img, (0, 0), self.params.sigma)

        cv2.imshow("Test", img)

        return self._track_ellipses(img)

    def _track_ellipses(self, img: np.ndarray):
        try:
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
