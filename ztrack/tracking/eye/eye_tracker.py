from abc import ABC

from ztrack.tracking.tracker import Params, Tracker


class EyeParams(Params):
    pass


class EyeTracker(Tracker, ABC):
    pass
