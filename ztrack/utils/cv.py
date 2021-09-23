from typing import Tuple

import cv2
import numpy as np
from decord import VideoReader
from tqdm import tqdm


def binary_threshold(img: np.ndarray, threshold: int) -> np.ndarray:
    return cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)[1]


def find_contours(img: np.ndarray) -> list:
    return cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]


def contour_distance(contour, point: tuple):
    return cv2.pointPolygonTest(cv2.convexHull(contour), point, True)


def contour_center(contour) -> Tuple[float, float]:
    m = cv2.moments(contour)
    x = m["m10"] / m["m00"]
    y = m["m01"] / m["m00"]
    return x, y


def gaussian_blur(img: np.ndarray, sigma: float):
    if sigma > 0:
        return cv2.GaussianBlur(img, (0, 0), sigma)
    else:
        return img.copy()


def nearest_contour(contours, point):
    return max(contours, key=lambda contour: contour_distance(contour, point))


def fit_ellipse(contour) -> Tuple[float, float, float, float, float]:
    hull = cv2.convexHull(contour)
    if len(hull) < 5:
        hull = contour
    (x, y), (a, b), theta = cv2.fitEllipse(hull)
    return x, y, b / 2, a / 2, theta - 90


def rgb2gray(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)


def video_median(
    video_path: str, n_frames_for_bg=300, verbose=False
) -> np.ndarray:
    vr = VideoReader(video_path)
    n_frames = len(vr)
    n_frames_for_bg = min(n_frames, n_frames_for_bg)
    idx = np.linspace(0, n_frames - 1, n_frames_for_bg).astype(int)
    frames = [
        rgb2gray(vr[i].asnumpy()) for i in (tqdm(idx) if verbose else idx)
    ]

    return np.median(frames, axis=0).astype(np.uint8)
