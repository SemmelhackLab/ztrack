from abc import ABC

from ztrack.tracking.tracker import Tracker
from ztrack.tracking.params import Params


class EyeParams(Params):
    pass


class EyeTracker(Tracker, ABC):
    pass
