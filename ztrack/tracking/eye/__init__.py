from ..tracker import NoneTracker
from .adaptive_threshold import AdaptiveThresholdEyeTracker
from .binary import BinaryEyeTracker
from .eyes_only import EyesOnlyTracker
from .multi_threshold import MultiThresholdEyeTracker

trackers = [
    NoneTracker,
    MultiThresholdEyeTracker,
    BinaryEyeTracker,
    AdaptiveThresholdEyeTracker,
    EyesOnlyTracker,
]
