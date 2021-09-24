from ..tracker import NoneTracker
from .contour import ContourFreeSwimTracker
from .sequential import SequentialFreeSwimTracker

trackers = [NoneTracker, SequentialFreeSwimTracker, ContourFreeSwimTracker]
