from pathlib import Path
from typing import Optional

import cv2
import numpy as np

import ztrack.utils.cv as zcv


class BackgroundSubtractionMixin:
    _verbose: int
    _bg: Optional[np.ndarray]
    _video_path: Optional[str]
    _is_bg_bright: bool

    def calculate_background(self, video_path):
        if self._verbose:
            print("Calculating background...")

        bg = zcv.video_median(video_path, verbose=self._verbose)
        cv2.imwrite(str(Path(video_path).with_suffix(".png")), bg)
        is_bg_bright = cv2.mean(bg)[0] > 127

        return is_bg_bright, bg
