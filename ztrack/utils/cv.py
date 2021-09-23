import cv2
import numpy as np


def binary_threshold(img: np.ndarray, threshold: int) -> np.ndarray:
    return cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)[1]


def find_contours(img: np.ndarray) -> list:
    return cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]


def contour_distance(contour: list, point: tuple):
    return cv2.pointPolygonTest(cv2.convexHull(contour), point, True)


def contour_center(c):
    m = cv2.moments(c)
    x = m["m10"] / m["m00"]
    y = m["m01"] / m["m00"]
    return x, y
