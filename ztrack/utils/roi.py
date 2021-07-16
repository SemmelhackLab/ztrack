import numpy as np


def relu(x):
    return max(0, x)


def normalize_roi(roi=None):
    if roi is not None:
        x, y, width, height = map(int, roi)
        x0, x1 = sorted(map(relu, (x, x + width)))
        y0, y1 = sorted(map(relu, (y, y + height)))
        return x0, y0, x1 - x0, y1 - y0


def roi2slice(roi=None, axis=0):
    if roi is None:
        return np.s_[:]
    x, y, width, height = roi
    return (np.s_[:],) * axis + np.s_[y: y + height, x: x + width]
