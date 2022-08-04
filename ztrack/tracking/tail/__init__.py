from ..tracker import NoneTracker
from .gradient import GradientTailTracker
from .gradient2 import GradientTailTracker2
from .sequential import SequentialTailTracker

trackers = [
    NoneTracker,
    SequentialTailTracker,
    GradientTailTracker,
    GradientTailTracker2,
]
