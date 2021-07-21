def wrap_degrees(deg: float) -> float:
    """Constrain angle to [180°, 180°).
    :param deg: Angle in degrees.
    :return: Angle in degrees in [180°, 180°).
    """
    return (deg + 180) % 360 - 180
