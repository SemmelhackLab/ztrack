from ..tracker import NoneTracker
from .binary import BinaryEyeTracker
from .multi_threshold import MultiThresholdEyeTracker

trackers = [NoneTracker, BinaryEyeTracker, MultiThresholdEyeTracker]
