from typing import Dict, Iterable, List, Type

from .eye import trackers as eye_trackers
from .tail import trackers as tail_trackers
from .tracker import Tracker

_trackers: Dict[str, Iterable[Type[Tracker]]] = {
    "Eye": eye_trackers,
}


def get_trackers() -> Dict[str, List[Tracker]]:
    return {key: [i() for i in value] for key, value in _trackers.items()}
