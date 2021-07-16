from abc import ABC

from ztrack.tracking.params import Params
from ztrack.tracking.tracker import Tracker


class EyeParams(Params):
    pass


class EyeTracker(Tracker, ABC):
    pass
