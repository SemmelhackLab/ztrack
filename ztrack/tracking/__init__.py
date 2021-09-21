from typing import Dict, Iterable, List, Type

from .eye import trackers as eye_trackers
from .tail import trackers as tail_trackers
from .tracker import Tracker

_trackers: Dict[str, Iterable[Type[Tracker]]] = {
    "eye": eye_trackers,
    "tail": tail_trackers,
}

_trackers_dict: Dict[str, Dict[str, Type[Tracker]]] = {
    group_name: {tracker.name(): tracker for tracker in trackers}
    for group_name, trackers in _trackers.items()
}


def get_trackers(verbose) -> Dict[str, List[Tracker]]:
    return {
        key: [i(verbose=verbose) for i in value]
        for key, value in _trackers.items()
    }


def get_trackers_from_config(config_dict, **kwargs) -> Dict[str, Tracker]:
    return {
        group_name: _trackers_dict[group_name][group_dict["method"]](
            group_dict["roi"], group_dict["params"], **kwargs
        )
        for group_name, group_dict in config_dict.items()
    }
