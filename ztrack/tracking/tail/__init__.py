from ..tracker import NoneTracker
# from .com import ComTailTracker
# from .gradient import GradientTailTracker
# from .gradient2 import GradientTailTracker2
from .sequential import SequentialTailTracker
# from .sequential2 import Sequential2
from .sequential_sato import SequentialSatoTailTracker

trackers = [
    NoneTracker,
    SequentialSatoTailTracker,
    SequentialTailTracker,
    # GradientTailTracker,
    # GradientTailTracker2,
    # ComTailTracker,
    # Sequential2,
]
