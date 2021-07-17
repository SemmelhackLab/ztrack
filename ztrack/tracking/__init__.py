from .eye import trackers as eye_trackers
from .tail import trackers as tail_trackers

_trackers = {"Eye": eye_trackers, "Tail": tail_trackers}


def get_trackers():
    return {key: [i() for i in value] for key, value in _trackers.items()}
