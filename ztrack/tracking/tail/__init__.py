from ..tracker import NoneTracker
from .gradient import GradientTailTracker
from .sequential import SequentialTailTracker

trackers = [NoneTracker, SequentialTailTracker, GradientTailTracker]
