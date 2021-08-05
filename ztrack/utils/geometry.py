import numpy as np


def wrap_degrees(deg: float) -> float:
    """Constrain angle to [180°, 180°).
    :param deg: Angle in degrees.
    :return: Angle in degrees in [180°, 180°).
    """
    return (deg + 180) % 360 - 180


def angle_diff(a, b):
    diff = (a - b) % (2 * np.pi)
    return np.min((diff, 2 * np.pi - diff), axis=0)
