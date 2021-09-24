from typing import Tuple

import cv2
import numpy as np
from decord import VideoReader
from scipy.interpolate import splev, splprep
from skimage.draw import circle_perimeter
from tqdm import tqdm

from .exception import TrackingError
from .geometry import angle_diff
from .math import split_int


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


def interpolate_tail(tail: np.ndarray, n_points: int) -> np.ndarray:
    tck = splprep(tail.T)[0]
    return np.column_stack(splev(np.linspace(0, 1, n_points), tck))


def sequential_track_tail(img, point, angle, theta, n_steps, length, n_points):
    h, w = img.shape
    tail = np.zeros((n_steps + 1, 2), dtype=int)
    tail[0] = point
    step_lengths = split_int(round(length), n_steps)
    for i in range(n_steps):
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
            raise TrackingError("Tail tracking failed")

        angle = angles[argmax]
        tail[i + 1] = point = points[argmax]

    return interpolate_tail(tail, n_points)


def rgb2gray_dark_bg_blur(img, sigma=0):
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    if cv2.mean(img)[0] > 127:
        img = cv2.bitwise_not(img)

    if sigma > 0:
        img = cv2.GaussianBlur(img, (0, 0), sigma)

    return img


def warp_img(
    img: np.ndarray, midpoint, heading: float, w: float, f: float, b: float
) -> np.ndarray:
    heading_rad = np.deg2rad(heading)
    v = np.array([np.cos(heading_rad), np.sin(heading_rad)])
    bbox_midpoint = midpoint + (f - b) * v
    h = f + b
    rect = (bbox_midpoint, (w, h), heading + 90)
    box = np.int0(cv2.boxPoints(rect))
    src_pts = box.astype("float32")
    dst_pts = np.array(
        [[0, h - 1], [0, 0], [w - 1, 0], [w - 1, h - 1]], dtype="float32"
    )

    T = cv2.getPerspectiveTransform(src_pts, dst_pts)

    return cv2.warpPerspective(img, T, (int(w), int(h)))


def orientation(src):
    moments = cv2.moments(src)
    return np.rad2deg(np.arctan2(2 * moments["mu11"], (moments["mu20"] - moments["mu02"])) / 2)
